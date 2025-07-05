/* Minimal Linker Script for STM32F4 QEMU C Unit Tests */
MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 256K /* Space for test code + Unity + src */
  RAM (xrw)  : ORIGIN = 0x20000000, LENGTH = 64K  /* Sufficient RAM for test execution */
}

ENTRY(Reset_Handler) /* Entry point must be Reset_Handler from startup_qemu_tests.c */

_estack = ORIGIN(RAM) + LENGTH(RAM); /* Define end of stack symbol */

SECTIONS
{
  .isr_vector : ALIGN(4)
  {
    KEEP(*(.isr_vector)) /* Vector table from startup_qemu_tests.c */
  } >FLASH

  .text : ALIGN(4)
  {
    *(.text)           /* .text sections (code) */
    *(.text*)          /* .text* sections (code) */
    *(.rodata)         /* .rodata sections (constants, strings) */
    *(.rodata*)        /* .rodata* sections */
    *(.glue_7)         /* glue arm to thumb */
    *(.glue_7t)        /* glue thumb to arm */
    *(.eh_frame)
    KEEP (*(.init))
    KEEP (*(.fini))
    _etext = .;        /* Global symbol at end of code */
  } >FLASH

  /* Initialized data section: copy from Flash to RAM */
  .data : ALIGN(4)
  {
    _sdata = .;        /* Create a global symbol at data start */
    *(.data)           /* .data sections */
    *(.data*)          /* .data* sections */
    _edata = .;        /* Define a global symbol at data end */
  } >RAM AT> FLASH     /* Specify LMA is in Flash */
  _sidata = LOADADDR(.data); /* Symbol for start of .data init values in Flash */


  .bss : ALIGN(4)      /* Uninitialized data section */
  {
    _sbss = .;         /* Define a global symbol at bss start */
    __bss_start__ = _sbss; /* Standard symbol */
    *(.bss)
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;         /* Define a global symbol at bss end */
    __bss_end__ = _ebss; /* Standard symbol */
  } >RAM

  /* Heap section (optional, if tests use malloc/free through a minimal heap) */
  /* For now, not defining a separate heap; it would come from remaining RAM */

  /* Minimum stack size (optional, if stack pointer is checked) */
  /* _min_stack_size = 0x200; */

  /DISCARD/ :
  {
    libc.a ( * )
    libm.a ( * )
    libgcc.a ( * )
  }
}
