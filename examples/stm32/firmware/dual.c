/* Two independent inputs: PA0 follows through PA5, PA1 follows through PA6. */
#define REG32(address) (*(volatile unsigned *)(address))
#define RCC_APB2ENR REG32(0x40021018u)
#define GPIOA_CRL REG32(0x40010800u)
#define GPIOA_IDR REG32(0x40010808u)
#define GPIOA_BSRR REG32(0x40010810u)

void Reset_Handler(void);
static void Fault_Handler(void) { for (;;) { __asm__ volatile ("nop"); } }
extern unsigned __stack_top__;

__attribute__((section(".isr_vector"), used))
const void * const vectors[16] = {
    &__stack_top__, Reset_Handler, Fault_Handler, Fault_Handler,
    Fault_Handler, Fault_Handler, Fault_Handler, 0,
    0, 0, 0, Fault_Handler, Fault_Handler, 0, Fault_Handler, Fault_Handler
};

void Reset_Handler(void)
{
    __asm__ volatile ("cpsid i");
    RCC_APB2ENR |= 1u << 2;  /* Enable GPIOA. */
    (void)RCC_APB2ENR;
    GPIOA_BSRR = (1u << 16) | (1u << 17) | (1u << 21) | (1u << 22);
    /* PA0/PA1 pull-downs and PA5/PA6 initially low. */
    GPIOA_CRL = (GPIOA_CRL & ~0x0ff000ffu) | 0x02200088u;
    /* PA0/PA1: input pull-up/down; PA5/PA6: push-pull output, 2 MHz mode. */
    GPIOA_BSRR = (1u << 21) | (1u << 22);  /* Drive both outputs low after configuration. */

    unsigned previous = 0;
    for (;;) {
        unsigned value = GPIOA_IDR & 3u;
        unsigned changed = value ^ previous;
        if (changed) {
            unsigned set_bits = (value & changed) << 5;
            unsigned reset_bits = ((~value & changed) << 5) << 16;
            GPIOA_BSRR = set_bits | reset_bits;
            previous = value;
        }
        /* Bound trace volume; this delay is neither a timer nor debounce. */
        for (unsigned i = 0; i < 800; ++i) {
            __asm__ volatile ("nop");
        }
    }
}
