#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <stdbool.h>
#include <stddef.h> // For size_t

// Checks if a string is null or empty.
bool is_string_empty(const char *str);

// Reverses a string in place.
// Returns the same pointer str.
// BEWARE: str must be mutable and null-terminated.
char* reverse_string(char *str);

#endif // STRING_UTILS_H
