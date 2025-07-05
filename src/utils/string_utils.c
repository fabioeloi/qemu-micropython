#include "utils/string_utils.h" // Adjusted path assuming include -I../../src will make "utils/string_utils.h" available
#include <string.h>   // For strlen
#include <stddef.h>   // For NULL if not implicitly available through other headers

bool is_string_empty(const char *str) {
    if (str == NULL || str[0] == '\0') {
        return true;
    }
    return false;
}

char* reverse_string(char *str) {
    if (str == NULL) {
        return NULL;
    }
    size_t len = strlen(str);
    if (len <= 1) {
        return str; // Nothing to reverse for empty or single char string
    }

    char *start = str;
    char *end = str + len - 1;
    char temp;

    while (start < end) {
        temp = *start;
        *start = *end;
        *end = temp;
        start++;
        end--;
    }
    return str;
}
