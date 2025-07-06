/* Standard Unity Internals Header File (Representative Content) */
#ifndef UNITY_INTERNALS_H
#define UNITY_INTERNALS_H

#include "unity.h" // Should include unity.h itself

// Standard C types
#include <stdint.h>
#include <stddef.h>

// Unity Float/Double types (can be configured)
#ifndef UNITY_FLOAT_TYPE
#define UNITY_FLOAT_TYPE float
#endif
#ifndef UNITY_DOUBLE_TYPE
#define UNITY_DOUBLE_TYPE double
#endif

// Integer types based on width (examples)
#ifndef UNITY_INT8
#define UNITY_INT8 int8_t
#endif
#ifndef UNITY_UINT8
#define UNITY_UINT8 uint8_t
#endif
#ifndef UNITY_INT16
#define UNITY_INT16 int16_t
#endif
#ifndef UNITY_UINT16
#define UNITY_UINT16 uint16_t
#endif
#ifndef UNITY_INT32
#define UNITY_INT32 int32_t
#endif
#ifndef UNITY_UINT32
#define UNITY_UINT32 uint32_t
#endif
#ifndef UNITY_INT64
#define UNITY_INT64 int64_t
#endif
#ifndef UNITY_UINT64
#define UNITY_UINT64 uint64_t
#endif

// Default integer type if not specified by width
#ifndef UNITY_INT_TYPE
#define UNITY_INT_TYPE UNITY_INT32
#endif
#ifndef UNITY_UINT_TYPE
#define UNITY_UINT_TYPE UNITY_UINT32
#endif


// Output character function (can be redefined by user)
#ifndef UNITY_OUTPUT_CHAR
#include <stdio.h> // For putchar if not redirected
#define UNITY_OUTPUT_CHAR(c) putchar(c)
#endif

#ifndef UNITY_OUTPUT_FLUSH
// #include <stdio.h> // For fflush if not redirected
// #define UNITY_OUTPUT_FLUSH() fflush(stdout)
#define UNITY_OUTPUT_FLUSH() // Often a no-op or platform specific
#endif

#ifndef UNITY_OUTPUT_START
#define UNITY_OUTPUT_START()
#endif

#ifndef UNITY_OUTPUT_COMPLETE
#define UNITY_OUTPUT_COMPLETE()
#endif


// Test Protect using setjmp/longjmp
#define UNITY_SUPPORT_SETJMP
#ifdef UNITY_SUPPORT_SETJMP
#include <setjmp.h>
#define TEST_PROTECT() (setjmp(Unity.AbortFrame) == 0)
#define TEST_ABORT() longjmp(Unity.AbortFrame, 1)
#else
#define TEST_PROTECT() 1
#define TEST_ABORT() return
#endif


// Display Styles
typedef enum
{
    UNITY_DISPLAY_STYLE_INT,
    UNITY_DISPLAY_STYLE_INT8,
    UNITY_DISPLAY_STYLE_INT16,
    UNITY_DISPLAY_STYLE_INT32,
    UNITY_DISPLAY_STYLE_INT64,
    UNITY_DISPLAY_STYLE_UINT,
    UNITY_DISPLAY_STYLE_UINT8,
    UNITY_DISPLAY_STYLE_UINT16,
    UNITY_DISPLAY_STYLE_UINT32,
    UNITY_DISPLAY_STYLE_UINT64,
    UNITY_DISPLAY_STYLE_HEX8,
    UNITY_DISPLAY_STYLE_HEX16,
    UNITY_DISPLAY_STYLE_HEX32,
    UNITY_DISPLAY_STYLE_HEX64,
    UNITY_DISPLAY_STYLE_POINTER,
    UNITY_DISPLAY_STYLE_FLOAT,
    UNITY_DISPLAY_STYLE_DOUBLE
} UNITY_DISPLAY_STYLE_T;


// Other internal macros, type definitions, and function prototypes
// that unity.c might need and unity.h might expose or use.

// Example: Stringification an formatting helpers
void UnityPrintFail(void);
void UnityPrintOk(void);
// ... and many more

#endif // UNITY_INTERNALS_H
