TEST_CODE1 = """public class Test
        {
            //test comment
            public static void main(String[] args)
            {	int x = 100;
            for(int i = 0; i < x; i++)
                System.out.println( i ); //prints out
            }

            public static double some_calc(int n)
            {	double res = 1;
                for(int i = 2; i <= n; i++)
                    res *= i;
                return res;
            }
    } """

TEST_CODE2 = """public class StringExample
    {	public static void main(String[] args)
        {	String s1 = "ss";
            int x = 31;
            String s2 = s1 + " " + x;

            System.out.println("s1: " + s1);
            System.out.println("s2: " + s2);

            //test comment

            x = 16;
            int y = 44;
            String s3 = x + y;
        }
    }"""

TEST_CODE3 = """public class Test
    {
        public static void main(String[] args) {
            printOnce();
            printOnce();
            printTwice();
        }

        public static void printOnce() {
            System.out.println("1");
        }

        public static void printTwice() {
            printOnce();
            printOnce();
        }
    }"""

TEST_CODE4 = """public class Deadlock {

        public static void main(String[] args) {
            Object a = new Object();
            Object b = new Object();
            Object c = new Object();

            System.out.println("hellp!");
            Thread t1 = new Thread() {
                public void run() {
                    synchronized(a) {
                        try {
                            Thread.sleep(1000);
                        }
                        catch(Exception e) {

                        }

                        synchronized(b) {
                            System.out.println("Occupying b!");
                        }
                    }}
            };
            t1.start();

            Thread t2 = new Thread() {
                public void run() {
                    synchronized(b) {
                    try {
                        Thread.sleep(1000);
                    }
                    catch(Exception e) {

                    }
                    synchronized(c) {
                        System.out.println("Occupying c!");
                    }
                }}
            };
            t2.start();
            Thread t3 = new Thread() {
                public void run() {
                    synchronized(c) {
                    try {
                        Thread.sleep(1000);
                    }
                    catch(Exception e) {

                    }
                    synchronized(a) {
                        System.out.println("Occupying a!");
                    }
                }}
            };
            t3.start();
        }

    }"""
