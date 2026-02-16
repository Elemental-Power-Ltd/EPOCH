#include <gtest/gtest.h>
#include <chrono>
#include <string>
#include <stdexcept>

#include "../epoch_lib/io/FileHandling.hpp"

/*
Some minimal testing of the ISO string functions 
to check that we can handle the sorts of strings the backend services will provide EPOCH
*/


TEST(Iso8601Test, RoundTripNow) {
    using namespace std::chrono;

    // Get current time
    auto now = system_clock::now();

    // Convert to ISO 8601
    std::string isoStr = toIso8601(now);

    // Convert back
    auto parsedTime = fromIso8601(isoStr);

    // Check difference in milliseconds
    auto diff = duration_cast<milliseconds>(now - parsedTime).count();

    // allow a small margin of error since system_clock::now()
    // could have small differences in precision/rounding.
    EXPECT_LE(std::abs(diff), 2) 
        << "Round-trip conversion should result in nearly the same time point";
}

TEST(Iso8601Test, ParseFixedString) {
    using namespace std::chrono;

    std::string fixedIso = "2022-01-01T00:00:00Z";

    std::chrono::system_clock::time_point tp;

    EXPECT_NO_THROW({
        tp = fromIso8601(fixedIso);
    }) << "fromIso8601 should successfully parse a valid ISO 8601 string.";
}

TEST(Iso8601Test, ParseFixedStringWithFractionalSeconds) {
    using namespace std::chrono;

    std::string fixedIso = "2022-01-01T00:00:00.000Z";

    auto tp = fromIso8601(fixedIso);
    std::string resultIso = toIso8601(tp);

    // our implementation returns fractional seconds
    // so here we can check the roundtrip from iso string to timepoint and back is exactly equal
    EXPECT_EQ(resultIso, fixedIso)
        << "toIso8601(fromIso8601(fixedIso)) should match original string";
}


TEST(Iso8601Test, HandlesInvalidString) {
    // Provide an invalid or malformed ISO 8601 string
    std::string invalidIso = "not-a-valid-timestamp";

    EXPECT_THROW({
        auto tp [[maybe_unused]] = fromIso8601(invalidIso);
    }, std::runtime_error);
}
