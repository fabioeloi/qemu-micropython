/* Standard Unity Header File (Representative Content) */
#ifndef UNITY_H
#define UNITY_H

#include <setjmp.h> // For TEST_PROTECT
#include <stddef.h> // For size_t, NULL
#include <stdint.h> // For intptr_t etc.

// Version (Example)
#define UNITY_VERSION_MAJOR 2
#define UNITY_VERSION_MINOR 5
#define UNITY_VERSION_BUILD 2
#define UNITY_VERSION ((UNITY_VERSION_MAJOR << 16) | (UNITY_VERSION_MINOR << 8) | UNITY_VERSION_BUILD)

// Standard Macros
#define UNITY_LINE_TYPE unsigned int
#define UNITY_COUNTER_TYPE unsigned int

#define UNITY_DISPLAY_STYLE_NORMAL
// #define UNITY_DISPLAY_STYLE_COMPACT

#ifndef UNITY_UINT_WIDTH
#define UNITY_UINT_WIDTH 32
#endif
#ifndef UNITY_INT_WIDTH
#define UNITY_INT_WIDTH 32
#endif

// Test Main
int UnityMain(int argc, const char* argv[], void (*runAllTests)(void));

// Test Cases
void UnityTestRunner(void(*SoFar)(void), const char* TestName, void(*Teardown)(void), void(*TestBody)(void), const UNITY_LINE_TYPE NumberOfCalls, const char* FuncName);

// Test Control
void UnityBegin(const char* filename);
int UnityEnd(void);
void UnityConcludeTest(void); // Called at the end of each test case
void UnitySetTestFile(const char *filename); // Usually called by RUN_TEST

// Test Output
void UnityPrint(const char* string);
void UnityPrintLen(const char* string, const UNITY_LINE_TYPE length);
void UnityPrintMask(const UNITY_LINE_TYPE mask, const UNITY_LINE_TYPE number);
void UnityPrintNumberByStyle(const UNITY_INT_TYPE number, const UNITY_DISPLAY_STYLE_T style);
// ... and many more print helpers

// Assertion Macros (a selection)
#define TEST_ASSERT_MESSAGE(condition, message)                             UnityAssert(((condition) != 0), message, __LINE__)
#define TEST_ASSERT(condition)                                              UnityAssert(((condition) != 0), NULL, __LINE__)
#define TEST_FAIL_MESSAGE(message)                                          UnityFail(message, __LINE__)
#define TEST_FAIL()                                                         UnityFail(NULL, __LINE__)
#define TEST_IGNORE_MESSAGE(message)                                        UnityIgnore(message, __LINE__)
#define TEST_IGNORE()                                                       UnityIgnore(NULL, __LINE__)
#define TEST_ONLY_IF(condition)                                             if (condition)

#define TEST_ASSERT_EQUAL_INT(expected, actual)                             UnityAssertEqualNumber((UNITY_INT_TYPE)(expected), (UNITY_INT_TYPE)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_INT)
#define TEST_ASSERT_EQUAL_INT8(expected, actual)                            UnityAssertEqualNumber((UNITY_INT_TYPE)(UNITY_INT8)(expected), (UNITY_INT_TYPE)(UNITY_INT8)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_INT8)
// ... many other integer types ...
#define TEST_ASSERT_EQUAL_UINT(expected, actual)                            UnityAssertEqualNumber((UNITY_INT_TYPE)(expected), (UNITY_INT_TYPE)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_UINT)
#define TEST_ASSERT_EQUAL_HEX8(expected, actual)                            UnityAssertEqualNumber((UNITY_INT_TYPE)(UNITY_INT8)(expected), (UNITY_INT_TYPE)(UNITY_INT8)(actual), NULL, __LINE__, UNITY_DISPLAY_STYLE_HEX8)

#define TEST_ASSERT_EQUAL_STRING(expected, actual)                          UnityAssertEqualString((const char*)(expected), (const char*)(actual), NULL, __LINE__)
#define TEST_ASSERT_EQUAL_STRING_LEN(expected, actual, len)                 UnityAssertEqualStringLen((const char*)(expected), (const char*)(actual), (UNITY_UINT32)(len), NULL, __LINE__)
#define TEST_ASSERT_EQUAL_MEMORY(expected, actual, len)                     UnityAssertEqualMemory((const void*)(expected), (const void*)(actual), (UNITY_UINT32)(len), 1, NULL, __LINE__)

#define TEST_ASSERT_NULL(pointer)                                           UnityAssertNull((const void*)(pointer), NULL, __LINE__)
#define TEST_ASSERT_NOT_NULL(pointer)                                       UnityAssertNotNull((const void*)(pointer), NULL, __LINE__)

#define TEST_ASSERT_TRUE(condition)                                         UnityAssert(((condition) != 0), NULL, __LINE__)
#define TEST_ASSERT_FALSE(condition)                                        UnityAssert(((condition) == 0), NULL, __LINE__)


// Test Runner Macros
#define UNITY_FIXTURE_SETUP(name)     void setUp(void)
#define UNITY_FIXTURE_TEARDOWN(name)  void tearDown(void)

#define UNITY_TEST_SUITE(name)        void name(void)
#define UNITY_TEST_CASE               void // For function definition

#define UNITY_BEGIN() UnityBegin(__FILE__)
#define UNITY_END()   UnityEnd()

// RUN_TEST calls UnityTestRunner
#define RUN_TEST(testFunc) UnityTestRunner(UnitySoFar, #testFunc, tearDown, testFunc, 1, __FILE__)

// Internal State (simplified access for test runner adaptation)
typedef struct _Unity UnityType;
extern UnityType Unity; // Definition in unity.c

struct _Unity {
    const char* TestFile;
    const char* CurrentTestName;
    const char* CurrentDetail1;
    const char* CurrentDetail2;
    UNITY_LINE_TYPE CurrentTestLineNumber;
    UNITY_COUNTER_TYPE NumberOfTests;
    UNITY_COUNTER_TYPE TestFailures;
    UNITY_COUNTER_TYPE TestIgnores;
    UNITY_COUNTER_TYPE CurrentTestFailed;
    UNITY_COUNTER_TYPE CurrentTestIgnored;
    jmp_buf AbortFrame;
};


#ifdef __cplusplus
extern "C" {
#endif

// Core functions (prototypes)
void UnityAssert(const int condition, const char* message, const UNITY_LINE_TYPE line);
void UnityFail(const char* message, const UNITY_LINE_TYPE line);
void UnityIgnore(const char* message, const UNITY_LINE_TYPE line);
void UnityAssertEqualNumber(const UNITY_INT_TYPE expected,
                            const UNITY_INT_TYPE actual,
                            const char* message,
                            const UNITY_LINE_TYPE line,
                            const UNITY_DISPLAY_STYLE_T style);
void UnityAssertEqualString(const char* expected,
                            const char* actual,
                            const char* message,
                            const UNITY_LINE_TYPE line);
// ... many more assertion function prototypes

void UnitySoFar(void); // Dummy for RUN_TEST

// For QEMU target execution (if needed by runner)
void qemu_exit(int code);

#ifdef __cplusplus
}
#endif

#endif // UNITY_H
