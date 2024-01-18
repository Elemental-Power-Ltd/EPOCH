#pragma once

#include <limits>
#include <mutex>
#include <optional>
#include <queue>

#include "../Definitions.h"

// Thread-safe queue

template<typename T>
class SafeQueue {
private:
    std::queue<T> queue;
    mutable std::mutex mutex;
    std::condition_variable cond;
    std::optional<float> minVal, maxVal;

public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(mutex);
        queue.push(value);
        cond.notify_one();
    }


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