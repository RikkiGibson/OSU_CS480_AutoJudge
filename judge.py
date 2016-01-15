#!/usr/bin/python
########################################################################
## judge.py - auto judge program for the Translators course in Oregon State University
## Author: Dezhong Deng
## Date: Jan 2016
## For more information of the course, please visit
## http://classes.engr.oregonstate.edu/eecs/winter2016/cs480/
########################################################################
import sys, os, filecmp
from collections import defaultdict

def run(code, inputfile, outputfile, hwname, iflinux):
    # print "on the code "+code
    tp = "timeout 0.1 " if iflinux else "gtimeout 0.1 " ## timeout prefix in commands
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
            command_compare = "diff test.out_c "+outputfile
        else:
            ## TODO: may change command_compare for future homworks
            ## like: ignoring blank lines, etc..
            pass
        result_compare = os.system(command_compare)
        if result_compare == 0:
            return 1, "passed! "
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
    iflinux = False
    if len(sys.argv) > 2 and (sys.argv[2]).lower() == "linux":
        iflinux = True
    
    testcasedir = "testcases_"+hwname
    submissiondir = "submissions_"+hwname

    submissionfiles = [f for f in os.listdir(submissiondir+"/") if os.path.isfile(submissiondir+"/"+f)]

    ## testcasefiles: without ".in" or ".out"
    testcasefiles = list(set([f.rsplit(".", 1)[0] for f in os.listdir(testcasedir+"/")
                         if os.path.isfile(os.path.join(testcasedir+"/", f))]))
    testcasefiles.sort()
    
    fullscore = len(testcasefiles)
    
    gradedict = defaultdict(lambda : (0, "No '.py' file detected.."))
    
    for file in submissionfiles:
        studentname = file.split("_", 1)[0]
        fileformat = file.rsplit(".", 1)[1]
        if fileformat == "py":
            print "------"
            print "File "+file
            score = 0
            commentlist = []
            for testcase in testcasefiles:
                print "Testcase " + testcase
                onescore, onecomment = run(submissiondir+"/"+file,
                                           testcasedir+"/"+testcase+".in",
                                           testcasedir+"/"+testcase+".out",
                                           hwname,
                                           iflinux
                )
                print "comment: " + onecomment
                score += onescore
                commentlist.append(testcase+":"+onecomment)
            gradedict[studentname] = (score, "\n".join(commentlist))
    for file in submissionfiles:
        studentname = file.split("_", 1)[0]
        if studentname not in gradedict:
            gradedict[studentname] = (0, "No '.py' file detected..")

    clear()

    fout = open("grades_"+hwname, "w")
    students = [x for x in gradedict]
    students.sort()
    for studentname in students:
        score, comment = gradedict[studentname]
        print >> fout, "------"
        print >> fout, studentname, score, "/", fullscore
        print >> fout, comment
    fout.close()
