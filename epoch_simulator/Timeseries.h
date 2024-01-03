#pragma once

#include <emmintrin.h>
#include <iostream>
#include <numeric>
#include <vector>

class year_TS {
public:
    year_TS(int int_timesteps = 8760): int_timesteps(int_timesteps), data(int_timesteps, 0.0f) {} // Constructor initializes a vector of 8760 hours float elements with a value of 0.0

    // Function to get the value at a specific index
    float getValue(unsigned int index) const {
        if (index < data.size()) {
            return data[index];
        }
        else {
            std::cerr << "Index out of range!" << std::endl;
            return -1; // Return an error value
        }
    }
    // Member function to set the value at a specific index
    void setValue(unsigned int index, float value) {
        if (index < data.size()) {
            data[index] = value;
        }
        else {
            std::cerr << "Index out of range!" << std::endl;
        }
    }
    // Function to get the entire data vector (returns a const reference to prevent modification)
    const std::vector<float>& getData() const {
        return data;
    }

    // Function to add data from another year_TS object element by element
  
    void addto(const year_TS& other) {
       
        auto it_other = other.data.cbegin();
        for (auto& val : data) {
            val += *it_other;
            ++it_other;
        }
    }

    static year_TS add(const year_TS& a, const year_TS& b) {
        // You might want to add size checks to ensure a.data.size() == b.data.size()

        year_TS result;
        result.data.resize(a.data.size());  // Resize the result data vector to hold the results

        size_t start = 0;
        size_t end = a.data.size();
        size_t i = start;
        size_t simd_end = start + ((end - start) / 4) * 4;

        for (; i < simd_end; i += 4) {
            __m128 vec1 = _mm_loadu_ps(&a.data[i]);
            __m128 vec2 = _mm_loadu_ps(&b.data[i]);
            __m128 res = _mm_add_ps(vec1, vec2);
            _mm_storeu_ps(&result.data[i], res);
        }

        // Handle remaining elements 
        for (; i < end; ++i) {
            result.data[i] = a.data[i] + b.data[i];
        }

        return result;
    }



    //// Static function to add data from two year_TS objects element by element
    //static year_TS add(const year_TS& a, const year_TS& b) {
    //    year_TS result;
    //    for (size_t i = 0; i < a.data.size(); ++i) {
    //        result.data[i] = a.data[i] + b.data[i];
    //    }
    //    return result;
    //}


    // Static function to subtract data from two year_TS objects element by element
   /* static year_TS subtract(const year_TS& a, const year_TS& b) {
        year_TS result;
        for (size_t i = 0; i < a.data.size(); ++i) {
            result.data[i] = a.data[i] - b.data[i];
        }
        return result;
    }*/
    // try SIMD elementwise for speed
    static year_TS subtract(const year_TS& a, const year_TS& b) {
        if (a.data.size() != b.data.size()) {
            std::cerr << "Data size mismatch!" << std::endl;
            return year_TS();  // Return an empty year_TS object or handle error appropriately
        }

        year_TS result;
        result.data.resize(a.data.size());

        size_t i = 0;
        size_t simd_end = (a.data.size() / 4) * 4;

        for (; i < simd_end; i += 4) {
            __m128 vec1 = _mm_loadu_ps(&a.data[i]);
            __m128 vec2 = _mm_loadu_ps(&b.data[i]);
            __m128 res = _mm_sub_ps(vec1, vec2);
            _mm_storeu_ps(&result.data[i], res);
        }

        // Handle remaining elements 
        for (; i < a.data.size(); ++i) {
            result.data[i] = a.data[i] - b.data[i];
        }

        return result;
    }


    void setTSvalues(const std::vector<float>& data) {
        std::size_t index = 0;
        for (const auto& val : data) {
            this->setValue(index, val);
            ++index;
        }
    }


    void scaleTSvalues(float scale_float) {
        for (auto& val : data) {
            val *= scale_float;
        }
    }

    // member function to scale this vector data by scale_float (say,kWp) AND OUTPUT NEW year_TS object
    year_TS scaleTSvalues_newTS(float scale_float) {
        year_TS scaled_TS_year;
        if (!data.empty()) {
            int index = 0;
            for (const auto& val : data) {
                float new_scaled_TSval = scale_float * val; //set the value to scaled value 
                scaled_TS_year.setValue(index, new_scaled_TSval);
                index++;
            }
        }
        return scaled_TS_year;
    }

    //year_TS scaleTSvalues_newTS(float scale_float) {
    //    year_TS scaled_TS_year;
    //    scaled_TS_year.data.resize(data.size());

    //    __m128 scale_vec = _mm_set1_ps(scale_float);

    //    size_t i = 0;
    //    size_t simd_end = (data.size() / 4) * 4;
    //    for (; i < simd_end; i += 4) {
    //        __m128 vec = _mm_loadu_ps(&data[i]);
    //        __m128 res = _mm_mul_ps(vec, scale_vec);
    //        _mm_storeu_ps(&scaled_TS_year.data[i], res);
    //    }

    //    // Handle remaining elements 
    //    for (; i < data.size(); ++i) {
    //        scaled_TS_year.data[i] = scale_float * data[i];
    //    }

    //    return scaled_TS_year;
    //}
#
    void setallTSvalues(float value) {
        for (auto& val : data) {
            val = value; //set the value to scaled value 
        }
    }

    // New member function to sum the values using std::accumulate
    float sum() const {
        return std::accumulate(data.begin(), data.end(), 0.0f);

    // Additional member functions can go here, e.g., to access or modify the data
}


private:
    std::vector<float> data;
    int int_timesteps;
};
