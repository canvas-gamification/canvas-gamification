import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class MainTest {
    static class Calculator {
        public int add(int x, int y) {
            return x + y;
        }
        // WRONG METHOD
        public int sub(int x, int y) {
            return x + y;
        }
    }

    private final Calculator calculator = new Calculator();

    @Test
    void addition() {
        assertEquals(2, calculator.add(1, 1), "Wrong add method");
    }

    @Test
    void subtraction() {
        assertEquals(1, calculator.sub(3, 2), "Wrong sub method");
    }
}
