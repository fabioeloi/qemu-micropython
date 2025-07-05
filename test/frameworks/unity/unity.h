// This is a placeholder for Unity's unity.h header file.
// In a real setup, this would contain all Unity assertion macros and declarations.

#ifndef UNITY_H
#define UNITY_H

#include <stdint.h> // For intptr_t

#define TEST_PROTECT() (1) // Simplified version for placeholder

// Basic assertion macro (simplified)
#define TEST_ASSERT_EQUAL_INT(expected, actual) UnityAssertEqualNumber((int)(expected), (int)(actual), NULL, __LINE__)
#define TEST_ASSERT_EQUAL_STRING(expected, actual) UnityAssertEqualString((const char*)(expected), (const char*)(actual), NULL, __LINE__)
#define TEST_ASSERT_NOT_NULL(pointer) UnityAssertNotNull((void*)(pointer), NULL, __LINE__)
#define TEST_ASSERT_NULL(pointer) UnityAssertNull((void*)(pointer), NULL, __LINE__)
#define TEST_ASSERT_TRUE(condition) UnityAssertTrue((condition), NULL, __LINE__)
#define TEST_ASSERT_FALSE(condition) UnityAssertFalse((condition), NULL, __LINE__)

#define TEST_FAIL_MESSAGE(message) UnityFail(message, __LINE__)
#define TEST_IGNORE_MESSAGE(message) UnityIgnore(message, __LINE__)


// Test case function macro (simplified)
#define TEST_CASE(funcName) void funcName(void)

// Test runner macros (simplified)
#define UNITY_BEGIN() UnityBegin(__FILE__)
#define UNITY_END() UnityEnd()
#define RUN_TEST(testFunc, linenum_unused) UnityDefaultTestRun(testFunc, #testFunc, (unsigned int)__LINE__)


// Setup and Teardown function prototypes (optional)
void setUp(void);
void tearDown(void);

// External declarations for placeholder unity.c
#ifdef __cplusplus
extern "C" {
#endif

extern unsigned int UnityLineNumber;
extern const char *UnityTestName;
extern unsigned int UnityTestCount;
extern unsigned int UnityFailureCount;
extern unsigned int UnityIgnoreCount;

void UnityBegin(const char* filename);
int UnityEnd(void); // Returns number of failures
void UnityAssertEqualNumber(const int expected, const int actual, const char* msg, const unsigned int line);
void UnityAssertEqualString(const char* expected, const char* actual, const char* msg, const unsigned int line);
void UnityAssertNotNull(const void* pointer, const char* msg, const unsigned int line);
void UnityAssertNull(const void* pointer, const char* msg, const unsigned int line);
void UnityAssertTrue(const int condition, const char* msg, const unsigned int line);
void UnityAssertFalse(const int condition, const char* msg, const unsigned int line);
void UnityFail(const char* message, const unsigned int line);
void UnityIgnore(const char* message, const unsigned int line);

void UnityDefaultTestRun(void (*pTestFunc)(void), const char* funcName, const unsigned int funcLine);

// For QEMU target execution
void qemu_exit(int code);


#ifdef __cplusplus
}
#endif

#endif // UNITY_H
