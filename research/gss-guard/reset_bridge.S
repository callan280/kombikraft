/* Authored fixture, NOT a recovered BMW bootloader. */
.section .text
.code16
.global _start
_start:
 cli
 xorw %ax,%ax
 movw %ax,%ds
 movw %ax,%es
 movw %ax,%ss
 lgdtw (0x8000+gdt_pointer-_start)
 movl $0x11,%eax
 movl %eax,%cr0
 .byte 0x66,0xea
 .long (0x8000+protected32-_start)
 .word 8
.code32
protected32:
 movw $0x10,%ax
 movw %ax,%ds
 movw %ax,%es
 movw %ax,%ss
 cld
 xorl %eax,%eax
 xorl %ebx,%ebx
 xorl %ecx,%ecx
 xorl %edx,%edx
 xorl %esp,%esp
 .byte 0xea
 .long 0x100000
 .word 8
.balign 8,0xcc
gdt:
 .quad 0
 /* Authored ROM descriptors have the architectural accessed bit preset. */
 .quad 0x00cf9b000000ffff
 .quad 0x00cf93000000ffff
gdt_end:
gdt_pointer:
 .word (gdt_end-gdt-1)
 .long (0x8000+gdt-_start)
.balign 16,0xcc
