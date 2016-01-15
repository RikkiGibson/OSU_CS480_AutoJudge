Auto Judge for Translators Course
======

This is an Auto Judge system for the grading of Translators course.

For more information of the course, please visit the site below.

http://classes.engr.oregonstate.edu/eecs/winter2016/cs480/

Install
------

* For Mac user, install "gtimeout" for Mac. You may use HomeBrew to install.

~~~
$ brew install coreutils
~~~

* For Linux/CentOS user, check "timeout" command.

Usage
------

* (for TAs) Download all students submissions on Canvas, then unzip to the directory "submissions_hwX".

* (for students) Put your python file into the directory "submissions_hwX" and rename it to "yourname_hwX.py".

~~~
$ cp hwX.py submissions_hwX/yourname_hwX.py
~~~

* Create/Edit test cases in the directory "testcases_hwX". Note that the test cases must be paired.

* Run this to check the grades. The grades are also in the file "grades_hwX".

~~~
Mac User $ sh exe.sh hwX
Others   $ sh exe.sh hwX linux
~~~

Creating/Contributing Test Cases
------

* Write a python program satisfies the syntax in the homework instruction.

* Make sure your program not cause out-of-requirement errors.

* Put your test case into the "testcase_hwX" folder. If your want to contribute your own test case, please put your name into the filename.

~~~
$ cat example.py > testcase_hwX/case_yourname_XX.in
$ python example.py > testcase_hwX/case_yourname_XX.out
~~~

* Contribute your test cases on Git.
