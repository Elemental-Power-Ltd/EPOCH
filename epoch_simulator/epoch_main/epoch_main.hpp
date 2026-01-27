#pragma once

#include <mimalloc.h>

#include "ArgHandling.hpp"
#include "../epoch_lib/io/FileConfig.hpp"
#include "../epoch_lib/io/EpochConfig.hpp"

// a single call to any mimalloc function is sufficient to replace the default allocator
int apply_mimalloc = mi_version();

static void simulate(const FileConfig& fileConfig, const EpochConfig& config);
