#pragma once

#include <mutex>
#include <optional>
#include <queue>

#include "Definitions.h"

inline std::optional<float> getSpecificFloat(const CustomDataTable& dataTable, const std::string& columnName) {
    for (const auto& column : dataTable) {
        if (column.first == columnName) {
            if (!column.second.empty()) {
                // Assuming you want the first value in the column for simplicity
                return column.second.front();
            }
            break;
        }
    }
    return std::nullopt; // Return std::nullopt if column not found or empty
}


// Thread-safe queue

template<typename T>
class SafeQueue {
private:
    std::queue<T> queue;
    mutable std::mutex mutex;
    std::condition_variable cond;
    std::optional<float> minVal, maxVal;

    // Function to update min and max values
    void updateMinMax(const CustomDataTable& value) {
        auto specificFloat = getSpecificFloat(value, "Your Column Name Here");
        if (specificFloat) {
            float val = specificFloat.value();
            if (!minVal || val < minVal.value()) minVal = val;
            if (!maxVal || val > maxVal.value()) maxVal = val;
        }
    }

public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(mutex);
        queue.push(value);
        cond.notify_one();
    }

    //void push(T value) {
    //    std::lock_guard<std::mutex> lock(mutex);
    //    //updateMinMax(value);
    //    queue.push(std::move(value));
    //    queue.push(value);
    //    cond.notify_one();
    //}


    bool pop(T& value) {
        std::unique_lock<std::mutex> lock(mutex);
        if (queue.empty()) {
            return false; // Return immediately if the queue is empty
        }
        value = queue.front();
        queue.pop();
        return true;
    }

    bool empty() {
        std::lock_guard<std::mutex> lock(mutex);
        return queue.empty();
    }

    bool try_pop(T& value) {
        std::unique_lock<std::mutex> lock(mutex, std::try_to_lock);
        if (!lock || queue.empty()) {
            return false; // Return immediately if the lock is not acquired or the queue is empty
        }
        value = queue.front();
        queue.pop();
        return true;
    }

    std::pair<float, float> getMinMax() const {
        std::lock_guard<std::mutex> lock(mutex);
        return { minVal.value_or(std::numeric_limits<float>::max()), maxVal.value_or(std::numeric_limits<float>::lowest()) };
    }

};