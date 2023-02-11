mkdir ./output

/usr/local/openjdk13/bin/javac -g -cp junit-platform-console-standalone-1.6.2.jar:canvas-gamification-junit-tests.jar {{user_code_filename}} MainTest.java >&2
/usr/local/openjdk13/bin/java -jar junit-platform-console-standalone-1.6.2.jar -cp canvas-gamification-junit-tests.jar --disable-ansi-colors --disable-banner --reports-dir=./output --details=none -cp . -c MainTest > /dev/null 2>/dev/null


tar -zxvf spotbugs-4.7.3.tgz > /dev/null 2> /dev/null
/usr/local/openjdk13/bin/java -jar spotbugs-4.7.3/lib/spotbugs.jar -textui -xml:withMessages=output/spotbugs.xml {{user_code_classname}} > /dev/null 2> /dev/null

cat ./output/TEST-junit-jupiter.xml 2> /dev/null
echo "==SEPARATOR=="
cat ./output/spotbugs.xml 2> /dev/null