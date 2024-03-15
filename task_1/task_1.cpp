#include <iostream>
#include <cmath>

#if defined(USE_FLOAT)
using DataType = float;
#elif defined(USE_DOUBLE)
using DataType = double;
#else
#error "Please define either USE_FLOAT or USE_DOUBLE during compilation."
#endif

int main() {
    const int size = 10000000;
    DataType array[size];

    for (int i = 0; i < size; ++i) {
        DataType angle = static_cast<DataType>(i) * 2 * M_PI / size;
        array[i] = std::sin(angle);
    }

    DataType sum = 0;
    for (int i = 0; i < size; ++i) {
        sum += array[i];
    }

    std::cout << "Sum: " << sum << std::endl;

    return 0;
}