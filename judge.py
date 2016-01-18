#!/usr/bin/python
########################################################################
## judge.py - auto judge program for the Translators course in Oregon State University
## Author: Dezhong Deng
## Date: Jan 2016
## For more information of the course, please visit
## http://classes.engr.oregonstate.edu/eecs/winter2016/cs480/
########################################################################
import sys, os
from collections import defaultdict

def run(code, inputfile, outputfile, hwname):
    # print "on the code "+code
    ifgtimeout = os.system("gtimeout --help >null 2>null2")
    tp = "gtimeout 1 " if ifgtimeout == 0 else "timeout 1 " ## timeout prefix in commands
    if hwname == "hw1":
        command_runlist = [
            "cat "+inputfile+" | "+tp+"python "+code+" > test.c",
            "clang test.c",
            "./a.out > test.out_c"
            ]
        command_runlist = map(lambda x:tp+x, command_runlist)
        command_run = " ; ".join(command_runlist)
    else:
        ## TODO: may change command_run for future homeworks
        pass
    result_run = os.system(command_run)
    
    if result_run == 0:
        if hwname == "hw1":
            command_compare = "diff -bd test.out_c "+outputfile
        else:
            ## TODO: may change command_compare for future homworks
            ## like: ignoring blank lines, etc..
            pass
        result_compare = os.system(command_compare)
        if result_compare == 0:
            if os.system("diff test.out_c "+outputfile) == 0:
                return 1, "passed! "
            else:
                return 0.9, "presentation error!"
        else:
            return 0, "result doesn't match.."
    elif result_run == 31744:
        return 0, "code running failed: time limit exceeded.."
    else:
        return 0, "code running failed: runtime error, error code "+str(result_run)+".."

def clear():
    command_clear = "rm test.c test.out_c a.out"
    result_clear = os.system(command_clear)
    return 0

if __name__ == "__main__":

    assert (len(sys.argv) >= 2)
    hwname = sys.argv[1]
    
    testcasedir = "testcases_%s/" % hwname
    submissiondir = "submissions_%s/" % hwname

    submissionfiles = [f for f in os.listdir(submissiondir) if os.path.isfile(submissiondir + f)]

    ## testcasefiles: without ".in" or ".out"
    testcasefiles = sorted(set([f.rsplit(".", 1)[0] for f in os.listdir(testcasedir)
                                if f[0] != "." and os.path.isfile(testcasedir + f)]))
    
    fullscore = len(testcasefiles)
    
    gradedict = defaultdict(lambda : (0, "No '.py' file detected.."))

    os.system("mkdir Excellent")
    
    for file in submissionfiles:
        studentname = file.split("_", 1)[0]
        fileformat = file.rsplit(".", 1)[1]
        if fileformat == "py":
            print "------"
            print "File "+file
            score = 0
            real_file = submissiondir+file
            commentlist = []
            for testcase in testcasefiles:
                print "Testcase " + testcase
                onescore, onecomment = run(real_file,
                                           testcasedir+testcase+".in",
                                           testcasedir+testcase+".out",
                                           hwname,
                )
                print "comment: " + onecomment
                score += onescore
                commentlist.append(testcase+":"+onecomment)
            gradedict[studentname] = (score, "\n".join(commentlist))
            if score == fullscore:
                os.system("cp -pr %s excellent/" % real_file)
                
    for file in submissionfiles:
        studentname = file.split("_", 1)[0]
        if studentname not in gradedict:
            gradedict[studentname] = (0, "No '.py' file detected..")

    clear()

    students = [x for x in gradedict]
    students.sort()

    ## print grades with comments
    fout = open("grades_"+hwname, "w")
    for studentname in students:
        score, comment = gradedict[studentname]
        print >> fout, "------"
        print >> fout, studentname, score, "/", fullscore,
        if score == fullscore:
            print >> fout, "excellent!"
        elif score >= fullscore * .8:
            print >> fout, "decent job!"
        else:
            print >> fout
        print >> fout, comment
    ## histogram stats
    print >> fout, "======"
    for i in range(fullscore+1):
        num = sum([1 for studentname in students if i <= gradedict[studentname][0] < i+1])
        if i == fullscore:
            print >> fout, "%d\t%d" % (i, num)
        else:
            print >> fout, "%d~%.2f\t%d" % (i, i+.99, num)
    fout.close()

