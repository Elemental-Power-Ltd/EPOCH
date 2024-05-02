#pragma once

#include <mimalloc.h>

// a single call to any mimalloc function is sufficient to replace the default allocator
int apply_mimalloc = mi_version();
