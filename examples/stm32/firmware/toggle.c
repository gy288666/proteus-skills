/* PA0 rising edges toggle PA5. Releasing the button preserves the output. */
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
    RCC_APB2ENR |= 1u << 2;                 /* Enable GPIOA. */
    (void)RCC_APB2ENR;
    GPIOA_BSRR = (1u << 16) | (1u << 21);  /* PA0 pull-down; PA5 initially low. */
    GPIOA_CRL = (GPIOA_CRL & ~0x00f0000fu) | 0x00200008u;
    /* PA0: input pull-up/down; PA5: push-pull output, 2 MHz mode. */
    GPIOA_BSRR = 1u << 21;  /* Explicitly drive PA5 low after enabling its output. */

    unsigned previous = 0;
    unsigned led = 0;
    for (;;) {
        unsigned value = GPIOA_IDR & 1u;
        if (value && !previous) {
            led ^= 1u;
            GPIOA_BSRR = led ? (1u << 5) : (1u << 21);
        }
        previous = value;
        /* Bound trace volume; this delay is neither a timer nor debounce. */
        for (unsigned i = 0; i < 800; ++i) {
            __asm__ volatile ("nop");
        }
    }
}
