import json
import statistics
import sys
from collections import Counter

import scipy
import os
import matplotlib.pyplot as plt
import numpy as np
import csv

from numpy.distutils.system_info import system_info

from src.plotCG import plotBar

'''
Given the energy  previously computed and summarized in energy_summary, it summarizes the results and outputs table for latex
'''


def exportResults(resultsFolder, execId, addTest, minNrExecutions=1, nameSet=""):
    pathEnergySummary = "{}/energy_summary/{}".format(resultsFolder, execId)
    ## TODO:
    pathTestEnergySummary = "/Users/matias/develop/energy-research/git-gr-experimental-data/energy_test_suite_summary/s_200_299/"  # "{}/energy_test_suite_summary/{}".format(resultsFolder, execId)

    energyFirstCorrectPatch = {}

    allApproaches = set()

    withLessThanMinNumberExec = []

    missingTestEnergyInformation = []

    dataPerTool = {}

    bugsWithLogs = set()
    bugsTbarPFL = set()

    discardedBugsOutOfScope = []


    energyFirstCorrectByProject = {}
    energyTestExecutionPerProject = {}

    energyTestExecutionPerBug = {}

    testAdded = []

    print("Adding test", addTest)
    hardData = readHard()
    dissectionData = readDissectionD4J()

    energyByRepairPatternCorrect = {}
    energyByRepairPatternIncorrect = {}

    ################# Detect  those  only considered in
    bugAssigments = {}
    for oneEnergyResult in os.listdir(pathEnergySummary):

        if ".DS_Store" == oneEnergyResult:
            continue

        f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

        energyRes = json.loads(f.read())
        f.close()

        kid = energyRes["TOOL_BUG_ID"]

        # print("Id {}".format(kid))

        kids = str(kid).strip().split("-")

        approach = kids[0]
        project = kids[1]
        bugid = kids[2]

        bid = "{}-{}".format(project, bugid)

        if bid not in bugAssigments:
            bugAssigments[bid] = []
        bugAssigments[bid].append(approach)

     ## Now search the bugs with only one approach and that approach is "LlamaRepairCL7bdcuda"
    onlyLlama = []
    for bid in bugAssigments:
        if len(bugAssigments[bid]) == 1 and bugAssigments[bid][0] == "LlamaRepairCL7bdcuda":
            onlyLlama.append(bid)

    print(f"Only Llama: {len(onlyLlama)}", onlyLlama)

    #############

    for oneEnergyResult in os.listdir(pathEnergySummary):

        if ".DS_Store" == oneEnergyResult:
            continue

        f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

        energyRes = json.loads(f.read())
        f.close()

        kid = energyRes["TOOL_BUG_ID"]

        # print("Id {}".format(kid))

        kids = str(kid).strip().split("-")

        approach = kids[0]
        project = kids[1]
        bugid = kids[2]

        bidd = "{}-{}".format(project, bugid)
        if bidd in  onlyLlama:
            print(f"Skipping {bidd} at LlamaRepair")
            continue

        if approach== "LlamaRepairCL7bdcuda":
            approach = "RepairLlama"


        if project not in energyFirstCorrectByProject:
            energyFirstCorrectByProject[project] = []

        if approach.lower() == "cardumen" or approach.lower() == "jkali":
            continue

        idbug = "{} {}".format(project, bugid)

        ### We check the bugid is one of those we consider
        #if idbug not in allBugsToConsider:
        #    print("NOT IN {}: {}".format(idbug,allBugsToConsider ))
        #    discardedBugsOutOfScope.append(kid)
        #    continue

        if approach.lower().startswith("plb") or approach.lower().startswith("codegen") or approach.lower().startswith(
                "codet") or approach.lower().startswith("incoder"):
            bugsWithLogs.add(idbug)
        elif approach.lower().startswith("tbar10c"):
            bugsTbarPFL.add(idbug)

        keyBug = "{}-{}".format(project, bugid)

        iDissection = None
        iRepairPatterns = None
        if keyBug in dissectionData:
            iDissection = dissectionData[keyBug]
            iRepairPatterns = iDissection["repairPatterns"]

            for aPatter in iRepairPatterns:
                if aPatter not in energyByRepairPatternCorrect:
                    energyByRepairPatternCorrect[aPatter] = []
                    energyByRepairPatternIncorrect[aPatter] = []
        #####
        iHard = None
        iTimeToFix = None
        iRelevantTestCount = None
        iStatementCoverage = None
        iPriority = None
        if keyBug in hardData:
            iHard = hardData[keyBug]
            iTimeToFix = float(iHard["TimeToFix"]) if iHard["TimeToFix"] != 'NA' else None
            iRelevantTestCount = float(iHard["RelevantTestCount"])
            iStatementCoverage = float(iHard["StatementCoverage"])
            iPriority = float(iHard["Priority"]) if iHard["Priority"] != 'NA' else None

        ## Retrieve consumption of test

        oneTestEnergyResult = "energy_test_summary_TestD4j-{}-{}.json".format(project, bugid)
        pathTestSummary = os.path.join(pathTestEnergySummary, oneTestEnergyResult)

        energyTestJules = None
        energyTestJulesNormalized = None
        #keyJoules = "Joules"  # if allEnergyJoules == True else "JoulesNormalized"

        if os.path.exists(pathTestSummary):
            f = open(pathTestSummary, "r")
            testEnergyRes = json.loads(f.read())
            f.close()

            energyTestJules = testEnergyRes["Joules"]["median"]
            energyTestJulesNormalized = testEnergyRes["JoulesNormalized"]["median"]


            timeTest = testEnergyRes["Time"]["median"]
            if project not in energyTestExecutionPerProject:
                energyTestExecutionPerProject[project] = []
            if testEnergyRes["JoulesNormalized"]["median"] > 1:
                if keyBug not in testAdded:
                    energyTestExecutionPerProject[project].append(testEnergyRes["JoulesNormalized"]["median"])
                    testAdded.append(keyBug)
                    energyTestExecutionPerBug[keyBug] = energyTestJules

            else:
                #print("Error test outlier {}".format(keyBug))
                pass
        else:
            print("Not existing {}".format(pathTestSummary))
            missingTestEnergyInformation.append(keyBug)
            continue

        #######Compute NCP:
        #### Obtain the ncp of the first patch from the traditional logs.
        ### The LLM based do not need them (we can count directly from the result path)
        pathToNCPSummary = "/Users/matias/develop/energy-research/git-gr-experimental-data/ncp/summary_2s_200_299"
        pfullncp = "ncp_{}-{}-{}.json".format(approach, project, bugid)
        pathncpfile = os.path.join(pathToNCPSummary, pfullncp)
        ncpFirstPatch = None
        ncpFirstCorrect = None
        ncpjson = None
        if approach != "Prapr":
            if os.path.exists(pathncpfile):
                fncp = open(pathncpfile)
                ncpjson = json.load(fncp)
                fncp.close()
                if len(ncpjson) > 0:
                    ncpFirstPatch = ncpjson[0]
                    # print("NCP first patch {}: {}".format(kid,ncpFirstPatch))
                elif len(energyRes["Correctness_Per_Patch"]) > 0:
                    print("Problems with the ncp of first patch {}".format(kid))

            # else:
            #    print("FILE NCP does not exist {}".format(pathncpfile))

        # Retrieve data from Bug
        key = "median" #" median" if "mean" not in  energyRes["Joules"] else "mean"
        totalEnergyJ = energyRes["Joules"][key] ### median
        totalEnergyJNormalized = energyRes["JoulesNormalized"]["median"]

        totalEnergyJStopFirst = energyRes["Joules"]["median"]
        totalEnergyJNormalizedStopFirst = energyRes["JoulesNormalized"]["median"]

        totalTime = energyRes["Time"]["median"]

        nrExec = energyRes["NrExecutions"]
        totalNrPatches = energyRes["NrPatches"]["median"]

        ## We check the number of execution
        if int(nrExec) < minNrExecutions:
            withLessThanMinNumberExec.append(kid)
            #print("With less than {} executions: {}".format(minNrExecutions, kid))
            continue

        isFirstCorrect = False
        firstPatchEnergyJ = None
        firstCorrectPatchEnergyJ = None
        firstPatchEnergyJNormalized = None
        firstCorrectPatchEnergyJNormalized = None
        allApproaches.add(approach)
        firstPatchExecutionTime = None
        firstCorrectPatchExecutionTime = None

        ## By default, all is wasted until the first patch is found
        wastedAfterFirst = totalEnergyJ
        wastedAfterFirstNormalized = totalEnergyJNormalized

        keyJoulesPerPatch = "Joules_Per_PatchMedian"  # if allEnergyJoules == True else "JoulesNormalized_Per_PatchMedian"

        nrPlausibleBeforeFirstCorrect = 0

        if len(energyRes["Correctness_Per_Patch"]) > 0:


            ## workarround of tbar

            if approach == "TBar10C":
                #print("Analyzing TBar10C")

                if len(energyRes["Joules_Per_PatchMedian"]) >= 10:
                    indexLastPatchtoConsider = 9
                  #  print("Rewriting total energy for {}  before {}".format(idbug, totalEnergyJ))
                    totalEnergyJ = energyRes["Joules_Per_PatchMedian"][indexLastPatchtoConsider]
                    totalEnergyJNormalized = energyRes["JoulesNormalized_Per_PatchMedian"][indexLastPatchtoConsider]

                    totalEnergyJStopFirst = energyRes["Joules_Per_PatchMedian"][indexLastPatchtoConsider]
                    totalEnergyJNormalizedStopFirst = energyRes["JoulesNormalized_Per_PatchMedian"][indexLastPatchtoConsider]

                    # Rewriting
                    wastedAfterFirst = totalEnergyJ
                    wastedAfterFirstNormalized = totalEnergyJNormalized




            for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
                if energyRes["Correctness_Per_Patch"][iAssess] == "C":

                    if iAssess == 0:
                        isFirstCorrect = True  ## MM 2024

                    if keyJoulesPerPatch in energyRes and iAssess < len(energyRes[keyJoulesPerPatch]):
                        firstCorrectPatchEnergyJ = energyRes["Joules_Per_PatchMedian"][iAssess]
                        firstCorrectPatchEnergyJNormalized = energyRes["JoulesNormalized_Per_PatchMedian"][iAssess]
                        firstCorrectPatchExecutionTime = energyRes["ExecutionTime_Per_PatchMedian"][iAssess]

                        if iDissection is not None:
                            for aPatter in iRepairPatterns:
                                energyByRepairPatternCorrect[aPatter].append(
                                    {"key": kid, "value": firstCorrectPatchEnergyJNormalized})

                    if ncpjson is not None:
                        ## for the traditional approach, we need to retrieve the ncp of the first correct patch
                        if iAssess < len(ncpjson):
                            ncpFirstCorrect = ncpjson[iAssess]
                            # print("NCP correct {}: {} {}".format(kid,ncpFirstCorrect, energyRes["Correctness_Per_Patch"] ))
                        else:
                            print("Problems with the ncp of correct patch {}".format(kid))
                    else:
                        ## for the llm based, we dont have the ncp of the first correct patch, but we have it in the LLM result file
                        if approach != "Prapr":
                            ncpFirstCorrect = iAssess + 1
                    ## Stops when we found the first correct patch
                    break

            for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
                ## MM2023
                if energyRes["Correctness_Per_Patch"][iAssess] in ("C", "I", "na"):
                    if keyJoulesPerPatch in energyRes and iAssess < len(energyRes[keyJoulesPerPatch]):
                        firstPatchEnergyJ = energyRes["Joules_Per_PatchMedian"][iAssess]
                        firstPatchEnergyJNormalized = energyRes["JoulesNormalized_Per_PatchMedian"][iAssess]
                        firstPatchExecutionTime = energyRes["ExecutionTime_Per_PatchMedian"][iAssess]

                        ###  If we stop at the first plausible patch, the total corresponds to the first plausible patch.
                        totalEnergyJStopFirst = firstPatchEnergyJ
                        totalEnergyJNormalizedStopFirst = firstPatchEnergyJNormalized

                        ## Compute wasted

                        wastedAfterFirst = totalEnergyJ - firstPatchEnergyJ
                        wastedAfterFirstNormalized = totalEnergyJNormalized - firstPatchEnergyJNormalized

                        if energyRes["Correctness_Per_Patch"][iAssess] in ("I", "na"):
                            if iDissection is not None:
                                for aPatter in iRepairPatterns:
                                    energyByRepairPatternIncorrect[aPatter].append(
                                        {"key": kid, "value": firstPatchEnergyJNormalized})

                    if ncpFirstPatch is None and approach != "Prapr":
                        ## The first patch ncp is computed here just for LLM approaches. That one from the LLM based is computed from the traditional logs.
                        ncpFirstPatch = iAssess + 1

                    break

            for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
                if energyRes["Correctness_Per_Patch"][iAssess] == "I":
                    nrPlausibleBeforeFirstCorrect += 1
                elif energyRes["Correctness_Per_Patch"][iAssess] == "C":
                    break


        ### Store
        #### Init structures
        if keyBug not in energyFirstCorrectPatch:
            energyFirstCorrectPatch[keyBug] = []

        ## Add FL info:
        if addTest:
            # print("Adding FL information")
            totalEnergyJ += energyTestJules
            totalEnergyJNormalized += energyTestJulesNormalized

            totalEnergyJStopFirst += energyTestJules
            totalEnergyJNormalizedStopFirst += energyTestJulesNormalized


            totalTime += timeTest

            if firstPatchEnergyJ is not None:
                firstPatchEnergyJ += energyTestJules
                firstPatchEnergyJNormalized += energyTestJulesNormalized
                firstPatchExecutionTime += timeTest
            else:
                wastedAfterFirst += energyTestJules
                wastedAfterFirstNormalized += energyTestJulesNormalized

            if firstCorrectPatchEnergyJ is not None:
                firstCorrectPatchEnergyJ += energyTestJules
                firstCorrectPatchEnergyJNormalized += energyTestJulesNormalized
                firstCorrectPatchExecutionTime += timeTest

        if firstCorrectPatchEnergyJ is not None:
            # energyFirstCorrectPatch[keyBug].append((approach, firstCorrectPatchEnergyJ))
            energyFirstCorrectPatch[keyBug].append((approach, firstCorrectPatchEnergyJNormalized))
            energyFirstCorrectByProject[project].append(firstCorrectPatchEnergyJNormalized)

        ### 		## TODO: Also with correct??
        #  if firstPatchEnergyJ is not None:
        # energyFirstPatch[keyBug].append((approach, firstPatchEnergyJ))
        # energyFirstPatch[keyBug].append((approach, firstPatchEnergyJNormalized))

        ## Now all
        if approach not in dataPerTool:
            dataPerTool[approach] = []

        dataPerTool[approach].append({"keyBug": keyBug, "approach": approach, "isFirstCorrect": isFirstCorrect,
                                      "totalEnergyJ": totalEnergyJ,
                                      "totalEnergyJNormalized": totalEnergyJNormalized,
                                      "totalEnergyJStopFirst": totalEnergyJStopFirst,
                                      "totalEnergyJNormalizedStopFirst": totalEnergyJNormalizedStopFirst,
                                      "firstPatchEnergyJ": firstPatchEnergyJ,
                                      "firstPatchEnergyJNormalized": firstPatchEnergyJNormalized,
                                      "firstPatchExecutionTime": firstPatchExecutionTime,
                                      "firstCorrectPatchEnergyJ": firstCorrectPatchEnergyJ,
                                      "firstCorrectPatchEnergyJNormalized": firstCorrectPatchEnergyJNormalized,
                                      "firstCorrectPatchExecutionTime": firstCorrectPatchExecutionTime,
                                      "nrPlausibleBeforeFirstCorrect": nrPlausibleBeforeFirstCorrect,
                                      "energyTestJules": energyTestJules,
                                      "energyTestJulesNormalized": energyTestJulesNormalized,
                                      "wastedAfterFirst" : wastedAfterFirst,
                                      "wastedAfterFirstNormalized": wastedAfterFirstNormalized,
                                      "ncpfirstPatch": ncpFirstPatch, "ncpFirstCorrect": ncpFirstCorrect,
                                      "repairPatterns": iRepairPatterns,
                                      "timeToFix": iTimeToFix,
                                      "relevantTestCount": iRelevantTestCount,
                                      "statementCoverage": iStatementCoverage,
                                      "priority": iPriority,

                                      })

    print("\n----Summary of Data--\n")

    ### Save NCP:
    print("Save NCP")
    keyN = "ncpfirstPatch"
    computeNCP(dataPerTool, "ncpfirstPatch")
    computeNCP(dataPerTool, "ncpFirstCorrect")

    withLessThanMinNumberExec = sorted(withLessThanMinNumberExec)

    print("\nWithout enough executions ({}) {}".format(len(withLessThanMinNumberExec), withLessThanMinNumberExec))

    print("Missing test information {} {}".format(len(set(missingTestEnergyInformation)),
                                                  set(missingTestEnergyInformation)))
    print("Not considered because out of scope ", sorted(discardedBugsOutOfScope))

    print("\nAll approaches considered ", allApproaches)

    print("\n----Results--------\n")

    ############ RESULTS
    if False:
        titleEnergyFirstPatch = "Comparison between approaches energy for First patch (X$>$Y means \# of times X is more efficient than Y)"
        print("\n***** Summary: " + titleEnergyFirstPatch)
        counterFasterFirstPatch = generateComparison(energyFirstPatch)
        # showCounter(counterFasterFirstPatch)
        printMatrics(allApproaches, counterFasterFirstPatch, caption=titleEnergyFirstPatch,
                     label="comparison:energy:firstpatch")

    ####

    titleEnergyFirstCorrectPatch = "Comparison between approaches energy for First Correct patch (X$>$Y means \# of times X is more efficient than Y)"
    print("\n***** Summary: " + titleEnergyFirstCorrectPatch)
    # print("energyFirstCorrectPatch",energyFirstCorrectPatch)
    counterFasterFirstCorrectPatch = generateComparison(energyFirstCorrectPatch)
    print("%%%Comparition first correct patch")
    printMatrics(allApproaches, counterFasterFirstCorrectPatch, caption=titleEnergyFirstCorrectPatch,
                 label="comparison:energy:firstcorrectpatch", addOverTotal=True)
    ###
    print("Now we print the details:")
    printMatrics(allApproaches, counterFasterFirstCorrectPatch, caption=titleEnergyFirstCorrectPatch,
                 label="comparison:energy:firstcorrectpatchDetail", addOverTotal=True, showDetail=True)

    ###########
    print("correlation time-energy\n")
    ##printCorrelation(allApproaches, listWithEnergyFirstPatch, listWithPatchEnergyTotal,  listWithPatchExecutionTximeFirstPatch, listWithPatchExecutionTime,
    ##				 pairsTimeEnergyPerTool)

    print("Main Table\n")

    totalBugs = 395
   # print("Main (2023)\n")
   # printMainTableValueMetrics(allApproaches, dataPerTool, printToTalEnergy=False, totalBugs=totalBugs)
    #print("Total (2024)\n")
    #printMainTableValueMetricsComplete2024(allApproaches, dataPerTool, isEarlyStop=False)

    print("Early stop (2024)\n")
    printMainTableValueMetricsComplete2024(allApproaches, dataPerTool, isEarlyStop=True)

    print("Complete (2024)\n")
    printMainTableValueMetricsComplete2024(allApproaches, dataPerTool, isEarlyStop=False)

    ### Rv1 Not sure for what we need. We can take from it the abount of the first patch that are correct.
    #print("%%Per patches (2024)\n")
    #printMainTableValueMetricsComplete2024PerPatches(allApproaches, dataPerTool)

    print("%%Correctness (2024)\n")
    printMainTableValueMetricsComplete2024PerPatchesCorrectness(allApproaches, dataPerTool)
    computeDifferences(allApproaches, dataPerTool)


    #### ###
    print("Comparison")
    printTableMannWPvalues(allApproaches, dataPerTool,
                           caption="Comparison of the distribution $Energy_{first\_patch}$ using the Mann-Whitney test. Cells show $p-values$, those with $p-values < 0.05$ (that is, rejection of $H_0$) are colored black..",
                           label="mannwhitneyutest")

    plotEnergyFirstPerProject(energyTestExecutionPerProject, name="test_{}".format(nameSet))
    plotEnergyFirstPerProject(energyFirstCorrectByProject, name="first_correct_{}".format(nameSet))
    plotEnergyFirstPerProject(energyTestExecutionPerProject, name="test_{}".format(nameSet), log=False)
    plotEnergyFirstPerProject(energyFirstCorrectByProject, name="first_correct_{}".format(nameSet), log=False)

    computeCorrelationPairs(dataPerTool, [("firstPatchExecutionTime", "firstPatchEnergyJNormalized"),
                                          ("firstCorrectPatchExecutionTime", "firstCorrectPatchEnergyJNormalized"),
                                          ("ncpfirstPatch", "firstPatchEnergyJNormalized"),
                                          ("ncpFirstCorrect", "firstCorrectPatchEnergyJNormalized"),
                                          ("timeToFix", "firstPatchEnergyJNormalized"),
                                          ("timeToFix", "firstCorrectPatchEnergyJNormalized"),
                                          ("relevantTestCount", "firstPatchEnergyJNormalized"),
                                          ("relevantTestCount", "firstCorrectPatchEnergyJNormalized"),
                                          ("statementCoverage", "firstPatchEnergyJNormalized"),
                                          ("statementCoverage", "firstCorrectPatchEnergyJNormalized"),
                                          ])

    computeCorrelationPairsSingle(dataPerTool, [("firstPatchExecutionTime", "firstPatchEnergyJNormalized"),
                                                # # ("firstCorrectPatchExecutionTime", "firstCorrectPatchEnergyJNormalized"),
                                                ("ncpfirstPatch", "firstPatchEnergyJNormalized"),
                                                #  ("ncpFirstCorrect", "firstCorrectPatchEnergyJNormalized"),
                                                ##	  ("timeToFix", "firstPatchEnergyJNormalized"),
                                                ("timeToFix", "firstCorrectPatchEnergyJNormalized"),
                                                #	#	  ("relevantTestCount", "firstPatchEnergyJNormalized"),
                                                #		  ("relevantTestCount", "firstCorrectPatchEnergyJNormalized"),
                                                #	#	  ("statementCoverage", "firstPatchEnergyJNormalized"),
                                                #		  ("statementCoverage", "firstCorrectPatchEnergyJNormalized"),
                                                ("priority", "firstCorrectPatchEnergyJNormalized")
                                                ])


    ### 2024 REV1
    printOverfittingProportion(allApproaches,dataPerTool)



    pretty = json.dumps(dataPerTool, indent=2)  #

    res = open("alldata_{}.json".format(sorted(list(allApproaches))[0]), mode='w')
    res.write(pretty)
    res.close()

def printOverfittingProportion(allApproaches, dataPerTool,inJoules = False):

    print("%%% Proportion overfitting")
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"


    print("\\begin{tabular}{| l |  r || r | r   || }")
    print("\hline")
    #\multicolumn{2}{c}{Patches}
    h = ("&  Patches &  $Energy_{overfitting}$ & Per total  " )

    h += "\\\\"
    print(h)

    h = "Approach &  \#Overfitting & "+unit+"  &   "
    h += "\\\\"
    print(h)
    print("\hline")

    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergyOverfitting = []
        listEnergyOverfittingOnlyIncorrect = []
        total = []
        allOverfittingPatches = 0
        for aInfoBugFromApproach in infoBugsOfApproch:
            nrIncorrect = aInfoBugFromApproach["nrPlausibleBeforeFirstCorrect"]
            allOverfittingPatches+=nrIncorrect
            energyFromIncorrect = aInfoBugFromApproach["energyTestJules"] * nrIncorrect
            listEnergyOverfitting.append(energyFromIncorrect)
            #print(f"{iApproach} {aInfoBugFromApproach['keyBug']} nr incorrect {nrIncorrect} energy {energyFromIncorrect} total {aInfoBugFromApproach['totalEnergyJ']}")
            total.append(aInfoBugFromApproach["totalEnergyJ"])
            if nrIncorrect > 0:
                listEnergyOverfittingOnlyIncorrect.append(aInfoBugFromApproach["totalEnergyJ"])


        energyTotalOverfitting = sum(listEnergyOverfitting)
        energyTotalOverfittingFromIncorrect = sum(listEnergyOverfittingOnlyIncorrect)
        sumTotal = sum(total)
        if not inJoules:
            energyTotalOverfitting /= (3600)
            sumTotal /= (3600)
            energyTotalOverfittingFromIncorrect /= (3600)

        #"{}  & {}  &  XXX{:0.1f}YYY ({:0.2f}\%) &  XXX{:0.1f}YYY ({:0.2f}\%)
        # "{}  & {}  &  XXX{:0.1f}YYY  & {:0.2f}\% &  {:0.2f}\%   "
        row = ("{}  & {}  &  XXX{:0.1f}YYY  & {:0.2f}\% ".format( #& XXX{:0.1f}YYY
                iApproach.replace("_", "-"),
                    allOverfittingPatches,

                 energyTotalOverfitting, (energyTotalOverfitting/sumTotal)*100,
                 #(energyTotalOverfitting / energyTotalOverfittingFromIncorrect) * 100,
                #energyTotalOverfittingFromIncorrect, (energyTotalOverfittingFromIncorrect / sumTotal) * 100,
                  #  sumTotal
            ))


        row += "\\\\"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")
        print(row)


    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "overfittingProportion" + "}")
    print("\end{table*}")
    print("\n\n")


def computeNCP(dataPerTool, keyN):
    for app in dataPerTool:
        values = []
        valuesAll = []
        outJ = {}
        pairs = []
        for d in dataPerTool[app]:
            if d[keyN] is not None:
                values.append(d[keyN])
                valuesAll.append(d["keyBug"])
                pairs.append((d["keyBug"], d[keyN]))

        if len(values) != 0:
            outJ = {"approach": app, "median": statistics.median(values), "mean": statistics.mean(values),
                    "pairs": pairs, "values": values, "bugs": valuesAll, }

            dirout = "./allNCP/{}".format(keyN)
            if not os.path.exists(dirout):
                os.makedirs(dirout)

            with open("./{}/ncp_{}.json".format(dirout, app), 'w', encoding='utf-8') as outfile:
                json.dump(outJ, outfile, indent=4, ensure_ascii=False)
        else:
            pass
            # print("Problems with NCP of", app)


#	pretty = json.dumps(dataPerTool, indent=2)#
#	res = open("alldata_{}.json".format(list(allApproaches)[0]), mode='w')
#	res.write(pretty)
#	res.close()


def analyzePatterns(energyByRepairPatternCorrect, energyByRepairPatternIncorrect):
    print("############ Repair patterns")
    print(energyByRepairPatternCorrect)
    print(energyByRepairPatternIncorrect)
    ## TODO: what have the most consuming energy in terms of Repair actions, test, etc

    ## Rank

    summaryPerTool = {}
    summary = {}
    for aPatter in energyByRepairPatternIncorrect:

        values = []
        valuesPerTool = {}
        for i in energyByRepairPatternIncorrect[aPatter]:
            values.append(i["value"])

            key = str(i["key"]).split("-")[0]

            if key not in valuesPerTool:
                valuesPerTool[key] = []
            valuesPerTool[key].append(i["value"])

        if len(values) == 0:
            print("No values for ", aPatter)
        else:
            summary[aPatter] = statistics.median(values)

            for key in valuesPerTool.keys():
                if key not in summaryPerTool:
                    summaryPerTool[key] = {}

                if len(valuesPerTool[key]) > 0:
                    summaryPerTool[key][aPatter] = statistics.median(valuesPerTool[key])

    ##
    print("\nnnGeneral ")
    from collections import Counter
    countertop1 = Counter()
    countertop5 = Counter()

    countertop10 = Counter()
    sortedPatterns = sorted(summary.items(), key=lambda item: item[1], reverse=True)

    repairPatterns = []
    for si in sortedPatterns:
        print("-->", si[0], si[1])
        repairPatterns.append(si[0])

    approaches = []
    for app in summaryPerTool:
        approaches.append(app)

    actionsPerApproaches = {}

    for app in summaryPerTool:
        print("---", app)

        sortedPatterns = sorted(summaryPerTool[app].items(), key=lambda item: item[1], reverse=True)

        i = 1
        values = []
        for si in sortedPatterns:
            print(app, si[0], si[1])
            values.append(si[0])

            if i == 1:
                countertop1.update([si[0]])
            if i <= 5:
                countertop5.update([si[0]])
            if i <= 10:
                countertop10.update([si[0]])

            i += 1
        for missing in repairPatterns:
            if missing not in values:
                values.append(missing)

        actionsPerApproaches[app] = values
        from scipy.stats import kendalltau
    import itertools
    combApproaches = itertools.combinations(approaches, r=2)
    for c in combApproaches:
        print(c[0], c[1])
        l1 = actionsPerApproaches[c[0]]
        l2 = actionsPerApproaches[c[1]]
        # print(len(l1), l1)
        # print(len(l2), l2)
        k = kendalltau(l1, l2)
        print(k)

    print(countertop1)
    for i in countertop1:
        print(i)
    print(countertop5)
    print(countertop10)
    # print(combApproaches)


def analyzeLLM(resultsFolder, execId):
    pathEnergySummary = "{}/energy_summary/{}".format(resultsFolder, execId)

    inferencePerApproach = {}
    allinferencePerApproach = {}
    perinferencePerApproach = {}
    perinferencePerApproachTotal = {}


    distHigh = []
    distLow = []

    ################# Detect  those  only considered in
    bugAssigments = {}
    for oneEnergyResult in os.listdir(pathEnergySummary):

        if ".DS_Store" == oneEnergyResult:
            continue

        f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

        energyRes = json.loads(f.read())
        f.close()

        kid = energyRes["TOOL_BUG_ID"]

        # print("Id {}".format(kid))

        kids = str(kid).strip().split("-")

        approach = kids[0]
        project = kids[1]
        bugid = kids[2]


        bid = "{}-{}".format(project, bugid)

        if bid not in bugAssigments:
            bugAssigments[bid] = []
        bugAssigments[bid].append(approach)

    ## Now search the bugs with only one approach and that approach is "LlamaRepairCL7bdcuda"
    onlyLlama = []
    for bid in bugAssigments:
        if len(bugAssigments[bid]) == 1 and bugAssigments[bid][0] == "LlamaRepairCL7bdcuda":
            onlyLlama.append(bid)

    print(f"Only Llama: {len(onlyLlama)}", onlyLlama)




    for oneEnergyResult in os.listdir(pathEnergySummary):

        if ".DS_Store" == oneEnergyResult:
            continue

        f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

        energyRes = json.loads(f.read())
        f.close()

        kid = energyRes["TOOL_BUG_ID"]

        print("Id {}".format(kid))

        kids = str(kid).strip().split("-")

        project = kids[1]
        bugid = kids[2]
        bidd = "{}-{}".format(project, bugid)
        if bidd in onlyLlama:
            print(f"Skipping {bidd} at LlamaRepair")
            continue


        approach = kids[0]
        if approach == "LlamaRepairCL7bdcuda":
            approach = "RepairLlama"



        if approach not in inferencePerApproach:
            inferencePerApproach[approach] = []
            perinferencePerApproach[approach] = []
            allinferencePerApproach[approach] = []
            perinferencePerApproachTotal[approach] = []

        if approach.lower().startswith("tbar"):
            continue

        idbug = "{} {}".format(project, bugid)

        numerador = energyRes["Inf_Joules"]["median"] # energyRes["Inf_JoulesNormalized"]["median"]

        allinferencePerApproach[approach].append({"key": kid, "value": numerador})

        ## 2024
        total = energyRes["Joules"]["median"]
        peri = numerador / total
        perinferencePerApproachTotal[approach].append({"key": kid, "value": peri, "total" : total , "numerador": numerador})


        if len(energyRes["Correctness_Per_Patch"]) > 0:

            for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
                if energyRes["Correctness_Per_Patch"][iAssess] == "C" or energyRes["Correctness_Per_Patch"][
                    iAssess] == "I":  ## added
                    if iAssess < len(energyRes["Joules_Per_PatchMedian"]):
                        ## Before was just the correct, now all patches (gross, not normalized as before)
                        denom =  energyRes["JoulesNormalized_Per_PatchMedian"][iAssess]

                        inferencePerApproach[approach].append(
                            {"key": kid, "value": numerador, "correct_pos": iAssess + 1})

                        peri = numerador / denom

                        perinferencePerApproach[approach].append(
                            {"key": kid, "value": peri, "correct_pos": iAssess + 1})

                        if str(kid).lower().startswith("incoder_6b") or str(kid).lower().startswith("codegen_6b"):

                            if peri > 0.5:
                                # print("-->",perinferencePerApproach)
                                distHigh.append(iAssess + 1)
                            else:
                                distLow.append(iAssess + 1)

                        break

    # plotDistInferenceEnergy(inferencePerApproach, color=None) # color="green"
    # plotDistInferenceEnergy(allinferencePerApproach, color=None) #color="red"
    #plotDistPercentageInferenceEnergy(perinferencePerApproach, name="percentageInferencePlausible")
    ## 2024
    #plotDistPercentageInferenceEnergy(perinferencePerApproachTotal, name="percentageInferenceTotal")

    for iApp in perinferencePerApproachTotal:
        sumTotal = 0
        for c in perinferencePerApproachTotal[iApp]:
           sumTotal += c["total"]

        print("sum total ", iApp, sumTotal/3600, len(perinferencePerApproachTotal[iApp]))

    for app in perinferencePerApproach:
        value = []
        for c in perinferencePerApproach[app]:
            value.append(c["value"])
        if len(value) != 0:
            print(app, statistics.median(value), statistics.quantiles(value))

    #compareInferenceVsVal(distHigh, distLow)

    pretty = json.dumps(inferencePerApproach, indent=2)
    res = open("inferencePerApproach.json", mode='w')
    res.write(pretty)
    res.close()

    pretty = json.dumps(allinferencePerApproach, indent=2)
    res = open("allinferencePerApproach.json", mode='w')
    res.write(pretty)
    res.close()

    pretty = json.dumps(perinferencePerApproach, indent=2)
    res = open("perinferencePerApproach.json", mode='w')
    res.write(pretty)
    res.close()

    pretty = json.dumps(perinferencePerApproachTotal, indent=2)
    res = open("perinferencePerApproachTotal.json", mode='w')
    res.write(pretty)
    res.close()

    # Initialize dictionaries to store sums
    approach_inference_sums = {}
    approach_val_sums = {}
    approach_sum = {}
    # Calculate sums for each approach
    for approach, items in perinferencePerApproachTotal.items():
        if approach == "TBar10C":
            continue
        numerador_sum = sum(item['numerador']/3600000 for item in items)
        total_sum = sum(item['total']/3600000 for item in items)
        approach_inference_sums[approach] = numerador_sum
        approach_val_sums[approach] = total_sum - numerador_sum
        approach_sum[approach] = total_sum

        # Sort approaches by the sum of numerador in descending order
    sorted_approaches = sorted(approach_sum.items(), key=lambda x: x[1], reverse=True)

    fontSizeTicks = 20
    fontSizeTLabels = 20
    fontSizeLegend = 14

    # Plotting
    plotBarsInfVal2(approach_inference_sums, approach_sum, approach_val_sums, fontSizeLegend, fontSizeTLabels,
                   fontSizeTicks, sorted_approaches)




def plotBarsInfVal(approach_inference_sums, approach_sum, approach_val_sums, fontSizeLegend, fontSizeTLabels,
                   fontSizeTicks, sorted_approaches):
    approach_names = [approach[0] for approach in sorted_approaches]
    inference_values = [approach_inference_sums[approach] for approach in approach_names]
    val_values = [approach_val_sums[approach] for approach in approach_names]
    total_sum_values = [approach_sum[approach] for approach in approach_names]
    x = np.arange(len(approach_names))
    bar_width = 0.2
    plt.bar(x, inference_values, bar_width, label='Inference')
    plt.bar(x + bar_width, val_values, bar_width, label='Validation')
    # Adding new bars for the total sum of Numerador and Total
    plt.bar(x + 2 * bar_width, total_sum_values, bar_width, label='Total (Inference + Validation)')
    plt.legend(fontsize=fontSizeLegend)
    plt.xlabel('Model', fontsize=fontSizeTLabels)
    plt.ylabel('Energy kWh', fontsize=fontSizeTLabels)
    # plt.title('Sum of numerador and total for each approach (sorted)')
    plt.xticks(x + bar_width / 2, approach_names, rotation=45, ha='right', fontsize=fontSizeTicks)
    plt.tight_layout()
    plt.show()
    plt.tight_layout()
    plt.savefig(
        'barInfValTotal.pdf',
        bbox_inches="tight")


def plotBarsInfVal2(approach_inference_sums, approach_sum, approach_val_sums, fontSizeLegend, fontSizeTLabels,
                   fontSizeTicks, sorted_approaches):
    approach_names = [approach[0] for approach in sorted_approaches]
    inference_values = [approach_inference_sums[approach] for approach in approach_names]
    val_values = [approach_val_sums[approach] for approach in approach_names]
    total_sum_values = [approach_sum[approach] for approach in approach_names]

    for x,y, z in zip(approach_names,inference_values,total_sum_values  ):
        print(f"{x} {y/z}")

    x = np.arange(len(approach_names))
    bar_width = 0.2
    #plt.bar(x, inference_values, bar_width, label='Inference')
    #plt.bar(x + bar_width, val_values, bar_width, label='Validation')
   # plt.bar(x, inference_values, bar_width, label='Inference')
   # plt.bar(x, val_values, bar_width, bottom=inference_values, label='Validation')
    bar_height = 0.6
    plt.barh(x, inference_values, bar_height, label='Inference',hatch='/')
    plt.barh(x, val_values, bar_height, left=inference_values, label='Validation', hatch='\\')

    # Add labels and legends
    plt.legend(fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.xlabel('Energy kWh', fontsize=12)
    plt.yticks(x, approach_names, fontsize=10)

    #plt.legend(fontsize=fontSizeLegend)
    #plt.xlabel('Model', fontsize=fontSizeTLabels)
    #plt.ylabel('Energy kWh', fontsize=fontSizeTLabels)
    ## plt.title('Sum of numerador and total for each approach (sorted)')
    #plt.xticks(x + bar_width / 2, approach_names, rotation=45, ha='right', fontsize=fontSizeTicks)
    #plt.tight_layout()
    #plt.show()
    #plt.tight_layout()
    plt.savefig(
        'barInfValTotalHorizontal.pdf',
        bbox_inches="tight")


def rankingLLL(resultsFolder, execId):
    pathEnergySummary = "{}/energy_summary/{}".format(resultsFolder, execId)

    rankingPL = {}
    rankingCorrect = {}

    for oneEnergyResult in os.listdir(pathEnergySummary):

        if ".DS_Store" == oneEnergyResult:
            continue

        f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

        energyRes = json.loads(f.read())
        f.close()

        kid = energyRes["TOOL_BUG_ID"]

        print("Id {}".format(kid))

        kids = str(kid).strip().split("-")

        approach = kids[0]
        project = kids[1]
        bugid = kids[2]

        if approach not in rankingPL:
            rankingPL[approach] = []
            rankingCorrect[approach] = []

        idbug = "{} {}".format(project, bugid)

        if len(energyRes["Correctness_Per_Patch"]) > 0:
            hasPlau = False
            for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
                if energyRes["Correctness_Per_Patch"][iAssess] == "C":
                    rankingCorrect[approach].append({"key": kid, "value": iAssess + 1})
                    if not hasPlau:
                        hasPlau = True
                        rankingPL[approach].append({"key": kid, "value": iAssess + 1})
                    break
                if energyRes["Correctness_Per_Patch"][iAssess] == "I":
                    rankingPL[approach].append({"key": kid, "value": iAssess + 1})
                    hasPlau = True

    for app in rankingPL:
        value = []
        for c in rankingPL[app]:
            value.append(c["value"])

        print(app, statistics.median(value))

    # plotDistInferenceEnergy(inferencePerApproach, color=None) # color="green"
    plotDistInferenceEnergy(rankingPL, color=None, ytitle="Ranking", file="rankingFirstPlausiblePatch")  # color="red"
    plotDistInferenceEnergy(rankingCorrect, color=None, ytitle="Ranking",
                            file="rankingFirstCorrectPatch")  # color="red"
    # plotDistPercentageInferenceEnergy(perinferencePerApproach)

    # compareInferenceVsVal(distHigh, distLow)

    pretty = json.dumps(rankingPL, indent=2)
    res = open("rankingPL.json", mode='w')
    res.write(pretty)
    res.close()

    pretty = json.dumps(rankingCorrect, indent=2)
    res = open("rankingCorrect.json", mode='w')
    res.write(pretty)
    res.close()


def compareInferenceVsVal(distHigh, distLow):
    fig, ax = plt.subplots()
    plots = ax.violinplot([distHigh, distLow], showmedians=True)
    print("distHigh ({}) {} ".format(len(distHigh), statistics.median(distHigh)))
    print("distLow ({}) {} ".format(len(distLow), statistics.median(distLow)))
    i = 0
    for pc in plots['bodies']:
        if i == 0:
            pc.set_facecolor("blue")
        if i == 1:
            pc.set_facecolor("green")
        i += 1
    labels = ["Energy_inf > 50%", "Energy_inf < 50%"]
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):  #
        vp = plots[partname]
        vp.set_edgecolor("Black")
    ax.set_xticks(np.arange(1, len(labels) + 1), labels=labels, fontsize=18)
    ax.set_xlim(0.25, len(labels) + 0.75)
    ax.set_ylabel('Ranking of patch', fontsize=22)
    plt.show()


def plotDistPercentageInferenceEnergy(inferenceEnergyNorm, color=None, name="test"):
    data, labels = formatData(inferenceEnergyNorm)

    fig, ax = plt.subplots()
    # Create a plot
    plots = ax.violinplot(data, showmedians=True)
    plt.yticks(fontsize=16, rotation=0)
    print("Energy: {}".format(inferenceEnergyNorm))
    # for pc in plots['bodies']:
    #	pc.set_facecolor("blue")

    if color is not None:
        for pc in plots['bodies']:
            pc.set_facecolor(color)
    else:
        i = 1
        for pc in plots['bodies']:
            if i <= 3:
                pc.set_facecolor("blue")
            elif i <= 6:
                pc.set_facecolor("green")
            elif i <= 8:
                pc.set_facecolor("red")
            else:
                pc.set_facecolor("violet")
            i += 1

    plots['cmedians'].set_colors("Black")
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):  #
        vp = plots[partname]
        vp.set_edgecolor("Black")
    ax.set_xticks(np.arange(1, len(labels) + 1), labels=labels, fontsize=22)  ##
    ax.set_xlim(0.25, len(labels) + 0.75)
    ax.set_ylabel('Energy Inference / Total', fontsize=18)  ##
    # ax.set_xlim(0.25, len(labels))
    # ax.set_xlabel('Sample name')
    plt.xticks(rotation=90)  #
    plt.savefig("{}.pdf".format(name), bbox_inches="tight")
    plt.show()


def formatData(inferenceEnergyNorm):
    data = []
    labels = []
    labelsOrdered = ['codegen_350M', 'codegen_2B', 'codegen_6B', 'codet5_small', 'codet5_base', 'codet5_large',
                     'incoder_1B', 'incoder_6B', 'plbart_base', 'plbart_large', 'RepairLlama', 'TBar10C']
    print(inferenceEnergyNorm.keys())
    for app in labelsOrdered:
        if len(inferenceEnergyNorm[app]) > 0:
            # labels.append(app.capitalize().replace("_", "-").replace("1b", "1B").replace("350m", "350M").replace("6b",
            #																									 "6B").replace(
            #	"large", "Large").replace("small", "Small").replace("base", "Base"))

            labels.append(app.capitalize().replace("_", "-").
                          replace("1b", "1B").
                          replace("350m", "350M").
                          replace("large", "L").
                          replace("6b", "6B").
                          replace("small", "S").
                          replace("base", "B").replace("Codegen", "CG").replace("Codet5", "cT5").replace("Incoder",
                                                                                                         "INC").replace(
                "Plbart", "PLB"))

            pd = []
            for p in inferenceEnergyNorm[app]:
                pd.append(p["value"])

            data.append(pd)
            # print(app, statistics.median(inferenceEnergyNorm[app]))
    print("labels {}".format(labels), len(labels), len(data))
    return data, labels


def plotDistInferenceEnergy(inferenceEnergyNorm, color="blue", ytitle="Energy on LLM Inference (Joules)", file="test"):
    data, labels = formatData(inferenceEnergyNorm)
    fig, ax = plt.subplots()
    # Create a plot
    plots = ax.violinplot(data, showmedians=True)
    plt.yticks(fontsize=16, rotation=0)
    print("Energy: {}".format(inferenceEnergyNorm))
    if color is not None:
        for pc in plots['bodies']:
            pc.set_facecolor(color)
    else:
        i = 1
        for pc in plots['bodies']:
            if i <= 3:
                pc.set_facecolor("blue")
            elif i <= 6:
                pc.set_facecolor("green")
            elif i <= 8:
                pc.set_facecolor("red")
            else:
                pc.set_facecolor("violet")
            i += 1

    plots['cmedians'].set_colors("Black")
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):  #
        vp = plots[partname]
        vp.set_edgecolor("Black")
    ax.set_xticks(np.arange(1, len(labels) + 1), labels=labels, fontsize=22)  ##18
    ax.set_xlim(0.25, len(labels) + 0.75)
    ax.set_ylabel(ytitle, fontsize=28)  ## 24
    # ax.set_xlim(0.25, len(labels))
    # ax.set_xlabel('Sample name')
    plt.xticks(rotation=90)
    plt.savefig("{}.pdf".format(file), bbox_inches="tight")
    plt.show()


def computeCorrelationPairs(data, listOfPairs):
    keys = {"firstPatchExecutionTime-firstPatchEnergyJNormalized": "T$_{fp}$-E$_{fp}$",
            "firstCorrectPatchExecutionTime-firstCorrectPatchEnergyJNormalized": "T$_{fcp}$-E$_{fcp}$",
            "ncpfirstPatch-firstPatchEnergyJNormalized": "NCP$_{fp}$-E$_{fp}$",
            "ncpFirstCorrect-firstCorrectPatchEnergyJNormalized": "NCP$_{fcp}$-E$_{fcp}$",
            "timeToFix-firstCorrectPatchEnergyJNormalized": "T2F-E$_{fcp}$",
            "relevantTestCount-firstCorrectPatchEnergyJNormalized": "Rtc-E$_{fcp}$",
            "statementCoverage-firstCorrectPatchEnergyJNormalized": "SC-E$_{fcp}$",
            "timeToFix-firstPatchEnergyJNormalized": "T2F-E$_{fp}$",
            "relevantTestCount-firstPatchEnergyJNormalized": "Rtc-E$_{fp}$",
            "statementCoverage-firstPatchEnergyJNormalized": "SC-E$_{fp}$"

            }

    print("\\begin{table*}[]")
    print("\centering")
    dataToSave = {}
    all = {}
    head = " "
    tabs = "|l"
    for p in listOfPairs:
        all[p] = ([], [])
        # head+= "& {}".format("-".join(p))
        head += "& {}".format(keys["-".join(p)])
        tabs += "|c"
    head += "\\\\"
    tabs += "|}"

    print("\\begin{tabular}{" + tabs)
    print("\\hline")
    print(head)
    print("\\hline")
    for iApproach in data.keys():
        # print("", iApproach)
        line = iApproach.replace("_", "")

        dataToSave[iApproach] = {}

        for pair in listOfPairs:
            # print(pair)
            list1 = []
            list2 = []
            listBugid = []

            dataOfPairApp = {}
            kf = "-".join(pair)
            dataOfPairApp["key"] = kf

            dataToSave[iApproach][kf] = dataOfPairApp

            for iBug in data[iApproach]:

                if (iBug[pair[0]] is None and iBug[pair[1]] is not None) or (
                        iBug[pair[0]] is not None and iBug[pair[1]] is None):
                    # print("ignoring for  ", iBug["keyBug"])
                    continue
                if iBug[pair[0]] is not None:
                    list1.append(iBug[pair[0]])
                if iBug[pair[1]] is not None:
                    list2.append(iBug[pair[1]])

                    listBugid.append(iBug["keyBug"])

            # print(pair, "l1",  list1, "\nl2", list2)
            if len(list1) != len(list2):
                print("different sizes for {} {} {} {}".format(iApproach, pair, len(list1), len(list2)))
                dataOfPairApp["pearsonr_message"] = "error:diffsize"
                dataOfPairApp["spearmanr_message"] = "error:diffsize"
                dataOfPairApp["l1"] = list1
                dataOfPairApp["l2"] = list2
                dataOfPairApp["lbugsid"] = listBugid
            else:
                all[pair][0].extend(list1)
                all[pair][1].extend(list2)
                if len(list1) > 1 and len(list2) > 1:
                    # print(list1)
                    # print(list2)
                    resultFPearson = scipy.stats.pearsonr(list1, list2)
                    resultFSpearman = scipy.stats.spearmanr(list1, list2)
                    dataOfPairApp["pearsonr"] = resultFPearson
                    dataOfPairApp["spearman"] = resultFSpearman
                    dataOfPairApp["l1"] = list1
                    dataOfPairApp["l2"] = list2
                    dataOfPairApp["lbugsid"] = listBugid

                    line += " & {:0.2f} ({})".format(resultFSpearman[0], len(list1))

                else:
                    line += " & fncp"
                    dataOfPairApp["pearsonr_message"] = "error:fewdata"
                    dataOfPairApp["spearmanr_message"] = "error:fewdata"
                    dataOfPairApp["l1"] = list1
                    dataOfPairApp["l2"] = list2
                    dataOfPairApp["lbugsid"] = listBugid
            # print("correlation {} {} {}".format(iApproach, pair, resultF[0]))
        line += "\\\\"
        print(line)

    print("\hline")
    end = "All "
    for p in listOfPairs:
        #resultF = scipy.stats.pearsonr(all[p][0], all[p][1])
        resultF = scipy.stats.spearmanr(all[p][0], all[p][1])
        end += " & {:0.2f} ({})".format(resultF[0], len(all[p][0]))
    end += "\\\\"
    print(end)

    print("\hline")

    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "correlations" + "}")
    print("\end{table*}")
    print("\n\n")

    pretty = json.dumps(dataToSave, indent=2)
    res = open("valuescorrelation_{}.json".format(list(data.keys())[0]), mode='w')
    res.write(pretty)
    res.close()


def computeCorrelationPairsSingle(data, listOfPairs, keyEnergy="firstPatchEnergyJNormalized"):
    keys = {"firstPatchExecutionTime-firstPatchEnergyJNormalized": "T$_{fp}$-E$_{fp}$",
            "firstCorrectPatchExecutionTime-firstCorrectPatchEnergyJNormalized": "T$_{fcp}$-E$_{fcp}$",
            "ncpfirstPatch-firstPatchEnergyJNormalized": "NCP$_{fp}$-E$_{fp}$",
            "ncpFirstCorrect-firstCorrectPatchEnergyJNormalized": "NCP$_{fcp}$-E$_{fcp}$",
            "timeToFix-firstCorrectPatchEnergyJNormalized": "T2F-E$_{fcp}$",
            "relevantTestCount-firstCorrectPatchEnergyJNormalized": "Rtc-E$_{fcp}$",
            "statementCoverage-firstCorrectPatchEnergyJNormalized": "SC-E$_{fcp}$",
            "timeToFix-firstPatchEnergyJNormalized": "T2F-E$_{fp}$",
            "relevantTestCount-firstPatchEnergyJNormalized": "Rtc-E$_{fp}$",
            "statementCoverage-firstPatchEnergyJNormalized": "SC-E$_{fp}$",
            "priority-firstCorrectPatchEnergyJNormalized": "Pr-E$_{fcp}$",

            }

    print("\\begin{table*}[]")
    print("\centering")
    dataToSave = {}
    all = {}
    allSum = {}
    head = " "
    tabs = "|l" if keyEnergy is None else "|l|c"
    for p in listOfPairs:
        all[p] = ([], [])
        # head+= "& {}".format("-".join(p))
        k = keys["-".join(p)]
        head += "& {} & {}".format(k.split("-")[0], k)
        tabs += "|c|c"
    head += "\\\\"
    tabs += "|}"

    print("\\begin{tabular}{" + tabs)
    print("\\hline")
    print(head)
    print("\\hline")
    vEnergyAll = []
    for iApproach in data.keys():
        # print("", iApproach)
        line = iApproach.replace("_", "")

        dataToSave[iApproach] = {}

        if keyEnergy is not None:
            vEnergy = []

            for iBug in data[iApproach]:

                if iBug[keyEnergy] is not None:
                    vEnergy.append(iBug[keyEnergy])
                    vEnergyAll.append(iBug[keyEnergy])
            if len(vEnergy) > 0:
                line += " & {:0.0f}".format(statistics.median(vEnergy))

        for pair in listOfPairs:
            # print(pair)
            list1 = []
            list2 = []
            listBugid = []

            dataOfPairApp = {}
            kf = "-".join(pair)
            dataOfPairApp["key"] = kf

            dataToSave[iApproach][kf] = dataOfPairApp

            for iBug in data[iApproach]:

                if (iBug[pair[0]] is None and iBug[pair[1]] is not None) or (
                        iBug[pair[0]] is not None and iBug[pair[1]] is None):
                    # print("ignoring for  ", iBug["keyBug"])
                    continue
                if iBug[pair[0]] is not None:
                    list1.append(iBug[pair[0]])
                if iBug[pair[1]] is not None:
                    list2.append(iBug[pair[1]])

                    listBugid.append(iBug["keyBug"])

            # print(pair, "l1",  list1, "\nl2", list2)
            if len(list1) != len(list2):
                print("different sizes for {} {} {} {}".format(iApproach, pair, len(list1), len(list2)))
                dataOfPairApp["pearsonr_message"] = "error:diffsize"

                dataOfPairApp["l1"] = list1
                dataOfPairApp["l2"] = list2
                dataOfPairApp["lbugsid"] = listBugid
            else:
                all[pair][0].extend(list1)
                all[pair][1].extend(list2)

                if len(list1) > 1 and len(list2) > 1:
                    # print(list1)
                    # print(list2)
                    resultF = scipy.stats.pearsonr(list1, list2)
                    dataOfPairApp["pearsonr"] = resultF
                    #tosem R1
                    resultF = scipy.stats.spearmanr(list1, list2)
                    dataOfPairApp["spearmanr"] = resultF

                    alpha = 0.05
                    if resultF[1] < alpha:
                        #print("Reject the null hypothesis: There is a significant correlation.")
                        dataOfPairApp["hypothesis_analysis_desc"] = "Reject the null hypothesis: There is a significant correlation."
                        dataOfPairApp["significant_corr"] = True
                    else:
                        #print("Fail to reject the null hypothesis: There is no significant correlation.")
                        dataOfPairApp[
                            "hypothesis_analysis_desc"] = "Fail to reject the null hypothesis: There is no significant correlation."
                        dataOfPairApp["significant_corr"] = False


                    line += " & {:0.2f} & {:0.2f} ({})".format(statistics.median(list1), resultF[0], len(list1))

                    dataOfPairApp["statsl1"] = {"metric": pair[0], "median": statistics.median(list1),
                                                "mean": statistics.mean(list1),
                                                "count": len(list1), "max": max(list1), "min": min(list1)}
                    dataOfPairApp["statsl2"] = {"metric": pair[1], "median": statistics.median(list2),
                                                "mean": statistics.mean(list2),
                                                "count": len(list2), "max": max(list2), "min": min(list2)}
                    dataOfPairApp["l1"] = list1
                    dataOfPairApp["l2"] = list2
                    dataOfPairApp["lbugsid"] = listBugid

                else:
                    line += " & fncp & fncp"
                    dataOfPairApp["pearsonr_message"] = "error:fewdata"
                    dataOfPairApp["spearmanr_message"] = "error:fewdata"
                    dataOfPairApp["l1"] = list1
                    dataOfPairApp["l2"] = list2
                    dataOfPairApp["lbugsid"] = listBugid
            # print("correlation {} {} {}".format(iApproach, pair, resultF[0]))
        line += "\\\\"
        print(line)

    print("\hline")
    end = "All "
    if keyEnergy is not None:
        end += " & {:0.0f}".format(statistics.median(vEnergyAll))
    dataToSave["All"] = {}
    for p in listOfPairs:
        dataOfPairApp = {}
        kf = "-".join(p)
        dataOfPairApp["key"] = kf

        dataToSave["All"][kf] = dataOfPairApp

        #resultF = scipy.stats.pearsonr(all[p][0], all[p][1])
        resultF = scipy.stats.spearmanr(all[p][0], all[p][1])
        end += " & {:0.1f} & {:0.2f} ({})".format(statistics.median(all[p][0]), resultF[0], len(all[p][0]))

        alpha = 0.05
        if resultF[1] < alpha:
            print("Reject the null hypothesis: There is a significant correlation.")
            dataOfPairApp[
                "hypothesis_analysis_desc"] = "Reject the null hypothesis: There is a significant correlation."
            dataOfPairApp["significant_corr"] = True
        else:
            print("Fail to reject the null hypothesis: There is no significant correlation.")
            dataOfPairApp[
                "hypothesis_analysis_desc"] = "Fail to reject the null hypothesis: There is no significant correlation."
            dataOfPairApp["significant_corr"] = False



    end += "\\\\"
    print(end)

    print("\hline")

    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "correlations" + "}")
    print("\end{table*}")
    print("\n\n")

    pretty = json.dumps(dataToSave, indent=2)
    res = open("valuescorrelation_{}.json".format(list(data.keys())[0]), mode='w')
    res.write(pretty)
    res.close()


def plotEnergyFirstPerProject(energyFirstCorrectByProject, name, log=True):
    print("\n********name ", name)
    data = []
    labels = [""]
    for project in sorted(energyFirstCorrectByProject):
        dataofproject = energyFirstCorrectByProject[project]
        dataofproject = [x/ 3600 for x in dataofproject]
        data.append(dataofproject)
        labels.append(project)
        print("-info-> project {} samples {} median {:.2f} mean {:.2f}  std {:.2f} min {:.2f} max {:.2f} ".format(project, len(dataofproject), statistics.median(dataofproject), statistics.mean(dataofproject), statistics.stdev(dataofproject), min(dataofproject),  max(dataofproject)) )
    # Extract Figure and Axes instance
    fig, ax = plt.subplots()
    # Create a plot
    plots = ax.violinplot(data, showmedians=True)
    plt.yticks(fontsize=16, rotation=0)
    plt.xticks(rotation=90)

    colors = ['Blue', 'Green', 'Purple', 'Orange', 'Olive', 'Pink']

    # Set the color of the violin patches
    for pc, color in zip(plots['bodies'], colors):
        pc.set_facecolor(color)

    plots['cmedians'].set_colors("Black")
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):  #
        vp = plots[partname]
        vp.set_edgecolor("Black")
    # https://stackoverflow.com/questions/26291479/changing-the-color-of-matplotlibs-violin-plots

    # ax.set_yscale("log", base=10)
    if log:
        ax.set_yscale("log")
    # Add title
    # ax.set_title('Distribution energy per project')
    ax.set_xticklabels(labels, fontsize=22)
    ax.set_ylabel('Energy (Wh)', fontsize=22)
    plotname = "energy_distr_{}_{}.pdf".format(name, "log" if log else "normal")
    print("Save plot", plotname)
    plt.savefig(plotname, bbox_inches="tight")


# https://matplotlib.org/stable/gallery/statistics/customized_violin.html

def computeDifferences(allApproaches, dataPerTool):
    allEnergyFirst = {}
    for approach in allApproaches:
        allEnergyFirst[approach] = []
        # print(dataPerTool[approach])
        for bug in dataPerTool[approach]:
            value = bug["firstPatchEnergyJNormalized"]
            if value is not None:
                allEnergyFirst[approach].append(value)

    for approachX in dataPerTool:
        timesRejectHo = 0
        timesAcceptH0 = 0

        listRejected = []
        listAccepted = []

        for approachY in dataPerTool:

            if approachX is not approachY:

                # print(approachX, approachY)
                # print(len(allEnergyFirst[approachX]), len(allEnergyFirst[approachY]))
                resultMannW = scipy.stats.mannwhitneyu(allEnergyFirst[approachX], allEnergyFirst[approachY])
                # print(resultMannW.pvalue)

                if resultMannW.pvalue < 0.05:
                    # print("Reject null")
                    timesRejectHo += 1

                else:
                    timesAcceptH0 += 1

        print("tool {} times reject (dif dist) {} times accept (sim dist) {}".format(approachX, timesRejectHo,
                                                                                     timesAcceptH0))


def printMainTableValueMetrics(allApproaches,
                               dataPerTool, printToTalEnergy=False, totalBugs=395, includeCorrect = False):
    # [approach].append((totalTime, totalEnergyJ, firstPatchEnergyJ, keyBug)

    # print("Number of samples {}".format(len(listAllExecutionTime)))

    print("TOTAL BUGS {}".format(totalBugs))

    print("\\begin{table*}[]")
    print("\centering")
    print("\\begin{tabular}{" + "| l | r| r||" +
          ("  r|  r| r  ||" if printToTalEnergy else "")
          + " r|  r| r  || r|  r| r  || r|  " + "}")
    print("\hline")
    # p
    # print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
    # print("&  &{First patch} & {Total execution}\\\\")
    # print("\cline{2-5}")

    print("&  \multicolumn{2}{c}{Patches} & " +
          ("  \multicolumn{3}{|c||}{$Energy_{Total}$} &" if printToTalEnergy else "")
          +
          # "   \multicolumn{3}{|c||}{$Energy_{first\_patch}$}  &  \multicolumn{3}{|c|| }{$Energy_{correct\_patch}$} & \multirow{2}{*}{CTA}\\\\"
          "   \multicolumn{2}{|c||}{$Energy_{first\_patch}$}  &  \multicolumn{2}{|c|| }{$Energy_{correct\_patch}$} & \multirow{2}{*}{Score}\\\\"
          )

    print("\\cline{2-12}" if printToTalEnergy else "\\cline{2-9}")

    print("Approach & \#Plausible &  \#Correct &  "
          + ("Gross (J) &  Net (J) &  NormTest  &" if printToTalEnergy else "")
          + "  Net (J) &  NormTest   &  Net (J) &  NormTest  & \\\\"
          # old22
          # + " Gross (J) &  Net (J) &  NormTest  & Gross (J) &  Net (J) &  NormTest  & \\\\"
          )
    print("\hline")
    import numpy as np
    import scipy.stats

    # print("All ", resultA)

    # print("\hdashline")
    ## by tool:
    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergAll = []
        listEnergRelative = []
        listEnerAllNorm = []

        listEnergFirst = []
        listEnergFirstNorm = []
        listEnergFirstRelative = []

        listEnergCorrectFirst = []
        listEnergCorrectFirstNorm = []
        listEnergCorrectFirstRelative = []

        listBugIds = []

        nrisFirstCorrect = 0
        for aInfoBugFromApproach in infoBugsOfApproch:

            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            listEnergAll.append(aInfoBugFromApproach["totalEnergyJ"])
            listEnerAllNorm.append(aInfoBugFromApproach["totalEnergyJNormalized"])
            listEnergRelative.append(aInfoBugFromApproach["totalEnergyJ"] / aInfoBugFromApproach["energyTestJules"])

            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None:
                # print("****\nBug id ", aInfoBugFromApproach["keyBug"])
                listEnergFirst.append(aInfoBugFromApproach["firstPatchEnergyJ"])
                listEnergFirstRelative.append(
                    aInfoBugFromApproach["firstPatchEnergyJNormalized"] / aInfoBugFromApproach[
                        "energyTestJulesNormalized"])
                listEnergFirstNorm.append(aInfoBugFromApproach["firstPatchEnergyJNormalized"])

            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])
                listEnergCorrectFirstRelative.append(
                    aInfoBugFromApproach["firstCorrectPatchEnergyJNormalized"] / aInfoBugFromApproach[
                        "energyTestJulesNormalized"])
                listEnergCorrectFirstNorm.append(aInfoBugFromApproach["firstCorrectPatchEnergyJNormalized"])

            listBugIds.append(aInfoBugFromApproach["keyBug"])

        listBugIds = sorted(listBugIds)

        medianTotalE = statistics.median(listEnergAll)
        stdTotalE = statistics.stdev(listEnergAll)
        medianEnergyAllNorm = statistics.median(listEnerAllNorm)
        medianTotalEnergyRelative2Test = statistics.median(listEnergRelative)

        medianFirst = statistics.median(listEnergFirst)
        stdFirst = statistics.stdev(listEnergFirst)
        medianFirstNorm = statistics.median(listEnergFirstNorm)
        medianFirstRelative = statistics.median(listEnergFirstRelative)

        ## Count plausibles
        plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)

        medianCorrect = "-"
        medianCorrectRelative = "-"

        if len(listEnergCorrectFirst) > 0:
            medianCorrect = statistics.median(listEnergCorrectFirst)
            medianCorrectRelative = statistics.median(listEnergCorrectFirstRelative)
            medianCorrectNorm = statistics.median(listEnergCorrectFirstNorm)
            if len(listEnergCorrectFirst) > 2:
                stdCorrect = statistics.stdev(listEnergCorrectFirst)
        else:
            print("No correct values!!!please check")
            medianCorrect = 0
            medianCorrectRelative = 0
            medianCorrectNorm = 0

        # if str(iApproach).lower().startswith("tbar"):

        accuracy = (corrects / totalBugs)
        # score =  (accuracy / medianCorrectRelative)  if medianCorrectRelative != 0 else 0
        # cta = medianTotalE / (accuracy * 10) if accuracy > 0 else 0

        ea = (medianCorrectNorm / (corrects)) if accuracy > 0 else 0

        metricToShow = ea
        ## previous measures (22)
        # score = accuracy / medianTotalE
        # cta =  medianTotalE / (accuracy * 10) if accuracy > 0 else 0

        chunkPlausible =   "{} ({})".format(plausibles, nrisFirstCorrect)  if includeCorrect else  "{}".format(plausibles)

        if printToTalEnergy:
            print("{} &  {} & {} "
                  " & {:0.0f} &  {:0.0f} &  {:0.2f} "
                  " & {:0.0f} &  {:0.0f} &  {:0.2f} "
                  " & {:0.0f} &  {:0.0f} &  {:0.2f} "
                  "   & {:0.1f} \\\\".format(iApproach, chunkPlausible, corrects,
                                             medianTotalE, medianEnergyAllNorm, medianTotalEnergyRelative2Test,
                                             medianFirst, medianFirstNorm, medianFirstRelative,
                                             medianCorrect, medianCorrectNorm, medianCorrectRelative,
                                             metricToShow
                                             ))
        else:

            print("{} &  {} & {} "
                  " &  {:0.0f} &  {:0.2f} "
                  " &  {:0.0f} &  {:0.2f} "
                  "   & {:0.1f} \\\\".format(iApproach, chunkPlausible, corrects,
                                             medianFirstNorm, medianFirstRelative,
                                             medianCorrectNorm, medianCorrectRelative,
                                             metricToShow))

    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "resultsMetrics" + "}")
    print("\end{table*}")
    print("\n\n")






def printMainTableValueMetricsComplete2024(allApproaches, dataPerTool, isEarlyStop=False, inJoules = False, includeCorrect=True):
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"
    ##  & Usage Idle  &  Usage Heavy

    print("\\begin{tabular}{| l | r | r || r | r  || }")
    print("\hline")

    h = ("&   \multicolumn{2}{c}{Patches} &  \multicolumn{1}{|c||}{$Energy_{Total}$} ")


    h += "\\\\"
    print(h)


    h = "Approach & \#Plausible &  \#Correct  & Gross ("+unit+") &  $\mTradeoffEnergyCorrect$" #

    h += "\\\\"
    print(h)
    print("\hline")

    approaches = []
    energyTotal = []
    allFirstCorrectPatches = []

    energyMean = []
    allRows = ""
    allRowsMobileComparison = ""
    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergAll = []
        listEnerAllNorm = []

        listEnergFirst = []
        listEnergCorrectFirst = []

        nrisFirstCorrect = 0
        nrCorrect = 0

        listEnergDifferenceAll = []

        nrBugs = len(infoBugsOfApproch)

        for aInfoBugFromApproach in infoBugsOfApproch:

            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            if not isEarlyStop:
                listEnergAll.append(aInfoBugFromApproach["totalEnergyJ"])
                listEnerAllNorm.append(aInfoBugFromApproach["totalEnergyJNormalized"])

                listEnergDifferenceAll.append(aInfoBugFromApproach["totalEnergyJ"] - aInfoBugFromApproach["totalEnergyJStopFirst"])

            else:
                listEnergAll.append(aInfoBugFromApproach["totalEnergyJStopFirst"])
                listEnerAllNorm.append(aInfoBugFromApproach["totalEnergyJNormalizedStopFirst"])


            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None:
                listEnergFirst.append(aInfoBugFromApproach["firstPatchEnergyJ"])

            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])
                nrCorrect+= 1

        # medianTotalE = statistics.median(listEnergAll)
        # medianEnergyAllNorm = statistics.median(listEnerAllNorm)

        totalEnergyApproach = sum(listEnergAll)
        totalEnergyApproachNorm = sum(listEnerAllNorm)
        totalDiff = sum(listEnergDifferenceAll)

        mobIdle = (totalEnergyApproach * 0.3861) / (3600 * 24) ## in days (3600 is seconds to hours, 24 is hours to days)
        # print("Total days 0.72 {}".format( )
        mobHeavy = (totalEnergyApproach * 0.15015) / (3600 * 24)

        medianIdle = (statistics.mean(listEnergAll) * 0.3861) / (3600 ) ## in hours
        medianHeavy = (statistics.mean(listEnergAll) * 0.15015) / (3600 ) ## in hours

        if not inJoules:
            totalEnergyApproach /=    (3600)
            totalEnergyApproachNorm /=    (3600)
            totalDiff /=    (3600)


        ## Count plausibles
        plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)
        ### In case we are in traditional, we just count the first correct, otherwise we put all correct.

        correctsToShow =  nrisFirstCorrect if "Avatar" in allApproaches else nrCorrect

        chunkPlausible = " {} & {}".format( plausibles, correctsToShow) if includeCorrect else "{}".format(plausibles)


        row = ("{} &  {} & XXX{:0.0f}YYY &  XXX{:0.1f}YYY".format(
            iApproach.replace("_", "-"), chunkPlausible,
            totalEnergyApproach,
            totalEnergyApproach/correctsToShow
        ))

        rowMobileComp= ("{} & XXX{:0.2f}YYY & XXX{:0.2f}YYY & XXX{:0.2f}YYY & XXX{:0.2f}YYY".format(
            iApproach.replace("_", "-"), mobIdle, medianIdle,  mobHeavy, medianHeavy
        ))

        approaches.append(iApproach)
        energyTotal.append(totalEnergyApproach)
        allFirstCorrectPatches.append(nrisFirstCorrect if "Avatar" in allApproaches else nrCorrect)
        energyMean.append(totalEnergyApproach/nrBugs)

        row += "\\\\ \n"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")

        allRows+= row

        rowMobileComp += "\\\\ \n"

        rowMobileComp = rowMobileComp.replace("XXX", "\\numprint{").replace("YYY", "}")
        allRowsMobileComparison+= rowMobileComp


    print(allRows)
    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "resultsMetrics" + "}")
    print("\end{table*}")
    print("\n\n")
    plotBar(approaches, energyTotal,  allFirstCorrectPatches , True if "Avatar" in allApproaches else False, "Total",
            titlePatches= "# bugs where first plausible is correct" if  "Avatar" in allApproaches else "# bugs with a correct patch")
    #plotBar(approaches, energyMean, allFirstCorrectPatches, True if "Avatar" in allApproaches else False, "Avg", titlePatches= "# bugs with correct patch")

    #print("\nMobileComparison Comp\n{}".format(allRowsMobileComparison))


def printMainTableRQ1TotalCorrect(allApproaches, dataPerTool, isEarlyStop=False, inJoules = False, includeCorrect=True):
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"
    ##  & Usage Idle  &  Usage Heavy

    print("\\begin{tabular}{| l | r | r || r | r  || }")
    print("\hline")

    h = ("&   \multicolumn{2}{c}{Patches} &  \multicolumn{1}{|c||}{$Energy_{Total}$} ")


    h += "\\\\"
    print(h)


    h = "Approach & \#Plausible &  \#Correct  & Gross ("+unit+") &  $\mTradeoffEnergyCorrect$" #

    h += "\\\\"
    print(h)
    print("\hline")

    approaches = []
    energyTotal = []
    allFirstCorrectPatches = []

    energyMean = []
    allRows = ""
    allRowsMobileComparison = ""
    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergAll = []
        listEnerAllNorm = []

        listEnergFirst = []
        listEnergCorrectFirst = []

        nrisFirstCorrect = 0
        nrCorrect = 0

        listEnergDifferenceAll = []

        nrBugs = len(infoBugsOfApproch)

        for aInfoBugFromApproach in infoBugsOfApproch:

            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            if not isEarlyStop:
                listEnergAll.append(aInfoBugFromApproach["totalEnergyJ"])
                listEnerAllNorm.append(aInfoBugFromApproach["totalEnergyJNormalized"])

                listEnergDifferenceAll.append(aInfoBugFromApproach["totalEnergyJ"] - aInfoBugFromApproach["totalEnergyJStopFirst"])

            else:
                listEnergAll.append(aInfoBugFromApproach["totalEnergyJStopFirst"])
                listEnerAllNorm.append(aInfoBugFromApproach["totalEnergyJNormalizedStopFirst"])


            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None:
                listEnergFirst.append(aInfoBugFromApproach["firstPatchEnergyJ"])

            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])
                nrCorrect+= 1

        # medianTotalE = statistics.median(listEnergAll)
        # medianEnergyAllNorm = statistics.median(listEnerAllNorm)

        totalEnergyApproach = sum(listEnergAll)
        totalEnergyApproachNorm = sum(listEnerAllNorm)
        totalDiff = sum(listEnergDifferenceAll)

        mobIdle = (totalEnergyApproach * 0.3861) / (3600 * 24) ## in days (3600 is seconds to hours, 24 is hours to days)
        # print("Total days 0.72 {}".format( )
        mobHeavy = (totalEnergyApproach * 0.15015) / (3600 * 24)

        medianIdle = (statistics.mean(listEnergAll) * 0.3861) / (3600 ) ## in hours
        medianHeavy = (statistics.mean(listEnergAll) * 0.15015) / (3600 ) ## in hours

        if not inJoules:
            totalEnergyApproach /=    (3600)
            totalEnergyApproachNorm /=    (3600)
            totalDiff /=    (3600)


        ## Count plausibles
        plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)
        ### In case we are in traditional, we just count the first correct, otherwise we put all correct.

        correctsToShow =  nrisFirstCorrect if "Avatar" in allApproaches else nrCorrect

        chunkPlausible = " {} & {}".format( plausibles, correctsToShow) if includeCorrect else "{}".format(plausibles)


        row = ("{} &  {} & XXX{:0.0f}YYY &  XXX{:0.1f}YYY".format(
            iApproach.replace("_", "-"), chunkPlausible,
            totalEnergyApproach,
            totalEnergyApproach/correctsToShow
        ))

        rowMobileComp= ("{} & XXX{:0.2f}YYY & XXX{:0.2f}YYY & XXX{:0.2f}YYY & XXX{:0.2f}YYY".format(
            iApproach.replace("_", "-"), mobIdle, medianIdle,  mobHeavy, medianHeavy
        ))

        approaches.append(iApproach)
        energyTotal.append(totalEnergyApproach)
        allFirstCorrectPatches.append(nrisFirstCorrect if "Avatar" in allApproaches else nrCorrect)
        energyMean.append(totalEnergyApproach/nrBugs)

        row += "\\\\ \n"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")

        allRows+= row

        rowMobileComp += "\\\\ \n"

        rowMobileComp = rowMobileComp.replace("XXX", "\\numprint{").replace("YYY", "}")
        allRowsMobileComparison+= rowMobileComp


    print(allRows)
    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "resultsMetrics" + "}")
    print("\end{table*}")
    print("\n\n")
    plotBar(approaches, energyTotal,  allFirstCorrectPatches , True if "Avatar" in allApproaches else False, "Total", titlePatches= "# bugs where first plausible is correct")
    plotBar(approaches, energyMean, allFirstCorrectPatches, True if "Avatar" in allApproaches else False, "Avg", titlePatches= "# bugs with correct patch")

    #pr


def printMainTableValueMetricsComplete2024PerPatches(allApproaches, dataPerTool,inJoules = False):
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"


    print("\\begin{tabular}{| l | r  |r || r| r || r | r || }")
    print("\hline")
    h = ("&  \multicolumn{2}{c}{Patches} &  \multicolumn{2}{|c||}{$Med Energy_{Total}$} &  \multicolumn{2}{|c||}{$Sum Energy_{Total}$} ")

    h += "\\\\"
    print(h)

    h = "Approach & \#Plausible &  \#Correct &  Gross ("+unit+") &  Net ("+unit+")  &  Gross ("+unit+") &  Net ("+unit+")"
    h += "\\\\"
    print(h)
    print("\hline")

    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergFirst = []
        listEnergFirstN = []
        listEnergCorrectFirst = []

        listWastedEnergy = []
        listWastedEnergyN = []

        nrisFirstCorrect = 0

        for aInfoBugFromApproach in infoBugsOfApproch:

            listWastedEnergy.append(aInfoBugFromApproach["wastedAfterFirst"])
            listWastedEnergyN.append(aInfoBugFromApproach["wastedAfterFirstNormalized"])

            #print(" {} {} wastedAfterFirst {}".format(iApproach, aInfoBugFromApproach["keyBug"], aInfoBugFromApproach["wastedAfterFirst"]))

            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None:
                listEnergFirst.append(aInfoBugFromApproach["firstPatchEnergyJ"])
                listEnergFirstN.append(aInfoBugFromApproach["firstPatchEnergyJNormalized"])

            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])

        medianTotalE = statistics.median(listEnergFirst)
        medianEnergyAllNorm = statistics.median(listEnergFirstN)


        total = sum(listEnergFirst) + sum(listWastedEnergy)
        totalN = sum(listEnergFirstN) + sum(listWastedEnergyN)

        if not inJoules:
            medianTotalE /= (3600)
            medianEnergyAllNorm /= (3600)
            total /= (3600)
            totalN /= (3600)

        ## Count plausibles
        plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)

        row = ("{} &  {} ({})& {}  & XXX{:0.0f}YYY &  XXX{:0.0f}YYY & XXX{:0.0f}YYY&  XXX{:0.0f}YYY".format(
                iApproach.replace("_", "-"), plausibles, nrisFirstCorrect, corrects,
                medianTotalE, medianEnergyAllNorm,  total , totalN
            ))


        row += "\\\\"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")
        print(row)

    # print("Total days 0.72 {}".format(mobIdle) )

    #    print("Total days 1.8 heavy {}".format(mobHeavy))

    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "medianPerPatch" + "}")
    print("\end{table*}")
    print("\n\n")

def printMainTableValueMetricsComplete2024PerPatchesCorrectness(allApproaches, dataPerTool,inJoules = False):
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"


    print("\\begin{tabular}{| l |  r || r | r | r  | r || }")
    print("\hline")
    #\multicolumn{2}{c}{Patches}
    h = ("&  Patches &  $Sum Energy_{correct}$ &  $Sum Energy_{Overfitting}$ &  $Sum Energy_{Unrepaired}$ & Total " )

    h += "\\\\"
    print(h)

    h = "Approach &  \#Correct &  Gross ("+unit+") &  Gros ("+unit+")  &  Gros ("+unit+") &  Gros ("+unit+")"
    h += "\\\\"
    print(h)
    print("\hline")

    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        #listEnergFirst = []
        listEnergyWithOverfitting = []
        #listEnergFirstN = []
        listEnergCorrectFirst = []
        #listEnergCorrectFirstNormalized = []

        listUnrepairedEnergy = []
        #listUnrepairedEnergyNormalized = []

        nrisFirstCorrect = 0
        total = []

        for aInfoBugFromApproach in infoBugsOfApproch:


            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            ## Let's take the energy of those that have a patch but it is not correct
            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None and aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is None:
                listEnergyWithOverfitting.append(aInfoBugFromApproach["totalEnergyJ"])
                #listEnergFirstN.append(aInfoBugFromApproach["firstPatchEnergyJNormalized"])

            elif aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])
                #listEnergCorrectFirstNormalized.append(aInfoBugFromApproach["firstCorrectPatchEnergyJNormalized"])

            ## We get the energy of the unrepaired bugs
            elif aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is None and aInfoBugFromApproach["firstPatchEnergyJ"] is None:
                listUnrepairedEnergy.append(aInfoBugFromApproach["totalEnergyJ"])
                #listUnrepairedEnergyNormalized.append(aInfoBugFromApproach["totalEnergyJNormalized"])
            else:
                print("REVISE CASE")
                sys.exit(1)
            total.append(aInfoBugFromApproach["totalEnergyJ"])

        medianCorrectTotalE =  statistics.median(listEnergCorrectFirst) if len(listEnergCorrectFirst) > 0 else 0
        #medianCorrectEnergyAllNorm = statistics.median(listEnergCorrectFirstNormalized) if len(listEnergCorrectFirst) > 0 else 0

        energyTotalCorrect = sum(listEnergCorrectFirst)
        #totalCorrectN = sum(listEnergCorrectFirstNormalized)

        totalUnrepair = sum(listUnrepairedEnergy)
        #totalUnrepairN = sum(listUnrepairedEnergyNormalized)

        totalOverfitting = sum(listEnergyWithOverfitting)

        sumTotal = sum(total)
        if not inJoules:
            medianCorrectTotalE /= (3600)
            #medianCorrectEnergyAllNorm /= (3600)
            energyTotalCorrect /= (3600)
            #totalCorrectN /= (3600)
            totalUnrepair /= (3600)
            #totalUnrepairN /= (3600)
            sumTotal /= (3600)
            totalOverfitting /= (3600)

        ## Count plausibles
        #plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)


        row = ("{}  & {}  &  XXX{:0.1f}YYY ({:0.2f}\%) & XXX{:0.1f}YYY ({:0.2f}\%) & XXX{:0.1f}YYY ({:0.2f}\%) & XXX{:0.1f}YYY".format(
                iApproach.replace("_", "-"), corrects,
                 energyTotalCorrect, (energyTotalCorrect/sumTotal)*100,
            totalOverfitting, (totalOverfitting / sumTotal) * 100,
            totalUnrepair, (totalUnrepair/sumTotal)*100,
            sumTotal
            ))


        row += "\\\\"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")
        print(row)



    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "medianPerPatch" + "}")
    print("\end{table*}")
    print("\n\n")


def printMainTableValueMetricsComplete2024PerPatchesCorrectnessR0(allApproaches, dataPerTool,inJoules = False):
    print("\\begin{table*}[]")
    print("\centering")
    unit = "J" if inJoules else "Wh"


    print("\\begin{tabular}{| l |  r || r | r | r || }")
    print("\hline")
    #\multicolumn{2}{c}{Patches}
    h = ("&  Patches &  $Sum Energy_{correct}$  &  $Sum Energy_{Unrepaired}$ & Total " )

    h += "\\\\"
    print(h)

    h = "Approach &  \#Correct &  Gross ("+unit+") &  Gros ("+unit+")  &  Gros ("+unit+")"
    h += "\\\\"
    print(h)
    print("\hline")

    for iApproach in sorted(allApproaches):
        infoBugsOfApproch = dataPerTool[iApproach]

        listEnergFirst = []
        listEnergFirstN = []
        listEnergCorrectFirst = []
        listEnergCorrectFirstNormalized = []

        listUnrepairedEnergy = []
        listUnrepairedEnergyNormalized = []

        nrisFirstCorrect = 0
        total = []

        for aInfoBugFromApproach in infoBugsOfApproch:


            if aInfoBugFromApproach["isFirstCorrect"]:
                nrisFirstCorrect += 1

            if aInfoBugFromApproach["firstPatchEnergyJ"] is not None:
                listEnergFirst.append(aInfoBugFromApproach["firstPatchEnergyJ"])
                listEnergFirstN.append(aInfoBugFromApproach["firstPatchEnergyJNormalized"])

            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is not None:
                listEnergCorrectFirst.append(aInfoBugFromApproach["firstCorrectPatchEnergyJ"])
                listEnergCorrectFirstNormalized.append(aInfoBugFromApproach["firstCorrectPatchEnergyJNormalized"])

            ## We get the energy of the unrepaired bugs
            if aInfoBugFromApproach["firstCorrectPatchEnergyJ"] is None:
                listUnrepairedEnergy.append(aInfoBugFromApproach["totalEnergyJ"])
                listUnrepairedEnergyNormalized.append(aInfoBugFromApproach["totalEnergyJNormalized"])

            total.append(aInfoBugFromApproach["totalEnergyJ"])

        medianCorrectTotalE =  statistics.median(listEnergCorrectFirst) if len(listEnergCorrectFirst) > 0 else 0
        medianCorrectEnergyAllNorm = statistics.median(listEnergCorrectFirstNormalized) if len(listEnergCorrectFirst) > 0 else 0


        energyTotalCorrect = sum(listEnergCorrectFirst)
        totalCorrectN = sum(listEnergCorrectFirstNormalized)

        totalUnrepair = sum(listUnrepairedEnergy)
        totalUnrepairN = sum(listUnrepairedEnergyNormalized)

        sumTotal = sum(total)
        if not inJoules:
            medianCorrectTotalE /= (3600)
            medianCorrectEnergyAllNorm /= (3600)
            energyTotalCorrect /= (3600)
            totalCorrectN /= (3600)
            totalUnrepair /= (3600)
            totalUnrepairN /= (3600)
            sumTotal /= (3600)

        ## Count plausibles
        plausibles = len(listEnergFirst)
        corrects = len(listEnergCorrectFirst)


        row = ("{}  & {}  &  XXX{:0.1f}YYY ({:0.2f}\%) & XXX{:0.1f}YYY ({:0.2f}\%) & XXX{:0.1f}YYY".format(
                iApproach.replace("_", "-"), corrects,
                 energyTotalCorrect, (energyTotalCorrect/sumTotal)*100,  totalUnrepair, (totalUnrepair/sumTotal)*100, sumTotal
            ))


        row += "\\\\"
        row = row.replace("XXX", "\\numprint{").replace("YYY", "}")
        print(row)

    # print("Total days 0.72 {}".format(mobIdle) )

    #    print("Total days 1.8 heavy {}".format(mobHeavy))

    print("\hline")
    print("\end{tabular}")
    print("\caption{" + " }")
    print("\label{tab:"
          + "medianPerPatch" + "}")
    print("\end{table*}")
    print("\n\n")


def printCorrelationDeprecated(allApproaches, listAllEnergyFirstPatch, listAllEnergyTotal,
                               listAllExecutionTimeFirstPatch, listAllExecutionTime,
                               pairsTimeEnergyPerTool):
    # print("Number of samples {}".format(len(listAllExecutionTime)))
    print("\\begin{table}[]")
    print("\centering")
    print("\\begin{tabular}{" + "| l | r| r | r | " + "}")
    print("\hline")
    # p
    # print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
    print("&  &{First patch} & {Total execution}\\\\")
    print("\cline{3-4}")
    print("Tool &  \#Repaired  & R spearman &     R spearman  \\\\")
    print("\hline")
    import numpy as np
    import scipy.stats
    #resultF = scipy.stats.pearsonr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
    #resultA = scipy.stats.pearsonr(listAllExecutionTime, listAllEnergyTotal)
    resultF = scipy.stats.spearmanr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
    resultA = scipy.stats.spearmanr(listAllExecutionTime, listAllEnergyTotal)

    # print("First ", resultF)
    # print("All ", resultA)
    print("All&  {} &   {:0.2f}  & {:0.2f}   \\\\".format(len(listAllExecutionTime), resultF[0], resultA[0]))
    print("\hdashline")
    ## by tool:
    for a in sorted(allApproaches):
        values = pairsTimeEnergyPerTool[a]
        listTimes = []
        listEnergAll = []
        listEnergFirst = []
        listTimesFirst = []
        listBugIds = []

        for v in values:
            # totalTime, totalEnergyJ, firstPatchExecutionTime, firstPatchEnergyJ
            listTimes.append(v[0])
            listEnergAll.append(v[1])
            listTimesFirst.append(v[2])
            listEnergFirst.append(v[3])
            listBugIds.append(v[4])

        listBugIds = sorted(listBugIds)
        # print("-- {} Number of samples {}: bugsid {}".format(a, len(listBugIds), listBugIds ))
        # print("-- {} Number of samples {}".format(a, len(listTimes)))
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
        #resultF = scipy.stats.pearsonr(listTimesFirst, listEnergFirst)
        #resultA = scipy.stats.pearsonr(listTimes, listEnergAll)  # , alternative='greater'

        resultF = scipy.stats.spearmanr(listTimesFirst, listEnergFirst)
        resultA = scipy.stats.spearmanr(listTimes, listEnergAll)

        #	print("First ", resultF)
        #	print("All ", resultA)
        print("{} & {} &  {:0.2f} & {:0.2f}  \\\\".format(a, len(listTimes), resultF[0], resultA[0]))

    print("\hline")
    print("\end{tabular}")
    print("\caption{"
          + "Pearson correlation between execution time and energy. The first column computes both metrics until the first patch is found, the second considers the energy and time for the complete execution." + "}")
    print("\label{tab:"
          + "correlationEnergyTime" + "}")
    print("\end{table}")
    print("\n\n")


def printCorrelationPvalue(allApproaches, listAllEnergyFirstPatch, listAllEnergyTotal, listAllExecutionTimeFirstPatch,
                           listAllExecutionTime,
                           pairsTimeEnergyPerTool):
    # print("Number of samples {}".format(len(listAllExecutionTime)))
    print("\\begin{table}[]")
    print("\centering")
    print("\\begin{tabular}{" + "| l | r | r | r | r | " + "}")
    print("\hline")
    # p
    print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
    print("\cline{2-5}")
    print("Tool & R Spearman &  P-value &   R Spearman &  P-value \\\\")
    print("\hline")
    import numpy as np
    import scipy.stats
    #resultF = scipy.stats.pearsonr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
    #resultA = scipy.stats.pearsonr(listAllExecutionTime, listAllEnergyTotal)

    resultF = scipy.stats.spearmanr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
    resultA = scipy.stats.spearmanr(listAllExecutionTime, listAllEnergyTotal)

    # print("First ", resultF)
    # print("All ", resultA)
    print("All& {:0.2f} & {:0.5f} & {:0.2f} & {:0.5f} \\\\".format(resultF[0], resultF[1], resultA[0], resultA[1]))
    print("\hdashline")
    ## by tool:
    for a in sorted(allApproaches):
        values = pairsTimeEnergyPerTool[a]
        listTimes = []
        listEnergAll = []
        listEnergFirst = []
        listTimesFirst = []
        listBugIds = []

        for v in values:
            # totalTime, totalEnergyJ, firstPatchExecutionTime, firstPatchEnergyJ
            listTimes.append(v[0])
            listEnergAll.append(v[1])
            listTimesFirst.append(v[2])
            listEnergFirst.append(v[3])
            listBugIds.append(v[4])

        print("-- {} Number of samples {}: bugsid {}".format(a, len(listTimes), listBugIds))
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
        resultF = scipy.stats.pearsonr(listTimesFirst, listEnergFirst)
        resultA = scipy.stats.pearsonr(listTimes, listEnergAll)  # , alternative='greater'

        resultF = scipy.stats.spearmanr(listTimesFirst, listEnergFirst)
        resultA = scipy.stats.spearmanr(listTimes, listEnergAll)  # , alternative='greater'

        #	print("First ", resultF)
        #	print("All ", resultA)
        print(
            "{} & {:0.2f} & {:0.5f} & {:0.2f} & {:0.5f} \\\\".format(a, resultF[0], resultF[1], resultA[0], resultA[1]))

    print("\hline")
    print("\end{tabular}")
    print("\caption{"
          + "Pearson correlation between execution time and energy. The first column computes both metrics until the first patch found, the second considers the energy and time for the complete execution." + "}")
    print("\label{tab:"
          + "correlationEnergyTime" + "}")
    print("\end{table}")
    print("\n\n")


def printMatrics(allApproach, count, caption="TO BE PUT", label="lab", showDetail=False, colored=True,
                 addOverTotal=False):
    print("\n\n")

    print("\\begin{table*}[]")
    print("\centering")

    # print("{ | l |}")

    aligheader = "| l | "

    bestApproaches = {}
    participationsApproaches = {}

    allApproach = list(allApproach)
   # allApproach.remove("Nopol")
    allApproach.sort()
    for ap in allApproach:
        aligheader += " c |"
        bestApproaches[ap] = 0
        participationsApproaches[ap] = 0

    print("\\begin{tabular}{" + aligheader + "}")
    # print(aligheader)
    print("\hline")
    firstrow = "&"
    for x in range(0, len(allApproach)):
        firstrow += " {} &".format(allApproach[x].replace("_", "-"))

    firstrow = (firstrow[0:len(firstrow) - 1]) + "\\\\"
    print(firstrow)
    print("\hline")
    for y in range(0, len(allApproach)):
        approachY = allApproach[y]
        rowS = approachY.replace("_","-") + " & "
        for x in range(0, len(allApproach)):

            approachX = allApproach[x]
            if approachX == approachY:
                row = "-"
            elif approachX in count and approachY in count[approachX]:
                # row = "{}-{}".format(len(count[approachX][approachY]) ,count[approachX][approachY] )

                otherRound = 0
                if approachY in count and approachX in count[approachY]:
                    otherRound = len(count[approachY][approachX])

                bestCurrent = len(count[approachX][approachY])
                if count[approachX][approachY] != 0:
                    participationsApproaches[approachX] = participationsApproaches[approachX] + 1

                if bestCurrent != 0:
                    percentage = (bestCurrent / (bestCurrent + otherRound)) * 100

                else:
                    percentage = 0

                if percentage > 50:
                    bestApproaches[approachX] = bestApproaches[approachX] + 1

                if colored:

                    if addOverTotal:
                        row = " \cca{" + "{:0.0f}".format(percentage) + "}\%" + " ({}/{}) ".format(bestCurrent, (
                                    bestCurrent + otherRound)) + (
                                  str(count[approachX][approachY]) if showDetail else "")
                    else:
                        row = " \cca{" + "{:0.0f}".format(percentage) + "}\%" + " ({}) ".format(bestCurrent) + (
                            str(count[approachX][approachY]) if showDetail else "")



                else:
                    row = "{} ({:0.2f}\%) ".format(bestCurrent, percentage) + (
                        str(count[approachX][approachY]) if showDetail else "")
            else:
                if approachX in count and not approachY in count[approachX] and approachY in count and approachX in \
                        count[approachY]:
                    otherRound = len(count[approachY][approachX])
                    row = "0/{}".format(otherRound)
                else:

                    row = 0
            rowS += " {} &".format(row)

        rowS = (rowS[0:len(rowS) - 1]) + "\\\\ \\hline"
        print(rowS)

    summaryRow = "\#comp $>$50\% &"
    print("\hline")
    for ap in allApproach:
        if participationsApproaches[ap] > 0:
            percBest = (bestApproaches[ap] / participationsApproaches[ap]) * 100
            summaryRow += "{} ({:0.1f}\%) ".format(bestApproaches[ap], percBest) + " &"
        else:
            summaryRow += "0 " + " &"

    summaryRow = (summaryRow[0:len(summaryRow) - 1]) + "\\\\"
    print(summaryRow)

    print("\hline")
    print("\end{tabular}")
    print("\caption{"
          + caption + "}")
    print("\label{tab:"
          + label + "}")
    print("\end{table*}")
    print("\n\n")


def printTableMannWPvalues(allApproach, dataPerTool, caption="TO BE PUT", label="lab", ez = True):
    print("\n\n")
    print(f"%%CorrelationMannWP firstCorrectPatchEnergyJ-  totalEnergyJ Effect size {ez}")
    allEnergyValues = {}
    for approach in allApproach:

        allEnergyValues[approach] = []
        # print(dataPerTool[approach])
        for bug in dataPerTool[approach]:
            #was commented for LLM, uncommented for Traditional
            #if bug["firstCorrectPatchEnergyJ"] is not None:

             #   allEnergyValues[approach].append(bug["firstCorrectPatchEnergyJ"])
            #else:
               allEnergyValues[approach].append(bug["totalEnergyJ"])

    print("\\begin{table*}[]")
    print("\centering")
    print("\\tiny")
    c = Counter()

    aligheader = "| l | "

    bestApproaches = {}
    participationsApproaches = {}

    allApproach = list(allApproach)
    allApproach.sort()
    for ap in allApproach:
        aligheader += " c |"
        bestApproaches[ap] = 0
        participationsApproaches[ap] = 0

    print("\\begin{tabular}{" + aligheader + "}")
    # print(aligheader)
    print("\hline")
    firstrow = "&"
    for x in range(0, len(allApproach)):
        firstrow += "\\rotatebox{90}{" + "{}".format(allApproach[x].replace("_","")) + "} &"

    firstrow = (firstrow[0:len(firstrow) - 1]) + "\\\\"
    print(firstrow)
    print("\hline")

    timesRejectHo = 0
    timesAcceptH0 = 0
    for y in range(0, len(allApproach)):
        approachY = allApproach[y]
        rowS = approachY.replace("_", "") + " & "

        #timesRejectHo = 0
        #timesAcceptH0 = 0


        for x in range(0, len(allApproach)):

            if False: #y > x: ## This is to make the table symmetric
                row = "-"

            else:
                approachX = allApproach[x]
                if approachX == approachY:
                    row = "-"
                else:

                    if approachX not in allEnergyValues or approachY not in allEnergyValues or len(
                            allEnergyValues[approachX]) < 2 \
                            or len(allEnergyValues[approachY]) < 2:
                        row = "na"
                    else:
                        resultMannW = scipy.stats.mannwhitneyu(allEnergyValues[approachX], allEnergyValues[approachY], alternative='two-sided')

                        if resultMannW.pvalue < 0.05:
                            # print("Reject null")
                            timesRejectHo += 1
                            if resultMannW.pvalue == 0:
                                row = "\cpv{" + "0" + "}"
                            else:

                                ## original
                                #    row = "\cpv{" + "{:0.2f}".format(resultMannW.pvalue) + "}"

                                from cliffs_delta import cliffs_delta

                                d, res = cliffs_delta(allEnergyValues[approachX], allEnergyValues[approachY])
                                #    row = "\cpv{" + "{:0.2f}".format(d) + "("+res[0].upper() +")}"
                                row = ("\cpv{\makecell{" + "{:0.2f}".format(resultMannW.pvalue) +
                                       " \\\\(" +"{:0.1f}".format(d) + " "+res[0].upper() +")"
                                       "}}")
                                c.update([res[0].upper()])

                        else:
                            timesAcceptH0 += 1
                            row = "{:0.2f}".format(resultMannW.pvalue)

                        ### NEW



            rowS += " {} &".format(row)

        rowS = (rowS[0:len(rowS) - 1]) + "\\\\ \\hline"
        print(rowS)

    print("\hline")
    print("\end{tabular}")
    print("\caption{"
          + caption + "}")
    print("\label{tab:"
          + label + "}")
    print("\end{table*}")

    print("%%Times reject H0 {}".format(timesRejectHo))
    print("%%Times accept H0 {}".format(timesAcceptH0))
    print("%%Effect size {}".format(c))

def showCounter(counterFasterTotalEnergy):
    for key in counterFasterTotalEnergy:
        for key2 in counterFasterTotalEnergy[key]:
            print("{} > {} : {} ".format(key, key2, len(counterFasterTotalEnergy[key][key2])))


"""
Data is a dic with list. Each list has a tuple with a tool and a value
"""


def generateComparison(data):
    counter = {}
    for aBugId in data:
        energyApproachesForBugid = data[aBugId]
        energyApproachesForBugid.sort(key=lambda a: a[1], reverse=False)

        # print("Sorted {}: {}".format(aBugId,energyApproachesForBugid ))

        if len(energyApproachesForBugid) > 1:

            for iApproach in range(0, len(energyApproachesForBugid)):

                for iAnother in range(iApproach + 1, len(energyApproachesForBugid)):
                    approach_faster = energyApproachesForBugid[iApproach][0]
                    value_faster = energyApproachesForBugid[iApproach][1]
                    approach_lower = energyApproachesForBugid[iAnother][0]
                    value_lower = energyApproachesForBugid[iAnother][1]
                    l = "{} > {}".format(approach_faster, approach_lower)
                    # counter[l] = counter.get(l, 0) + 1
                    if approach_faster not in counter:
                        counter[approach_faster] = {}

                    if approach_lower not in counter[approach_faster]:
                        # counter[approach_faster][approach_lower] = 0
                        counter[approach_faster][approach_lower] = []

                    counter[approach_faster][approach_lower].append((aBugId, value_faster,
                                                                     value_lower))  # counter[approach_faster][approach_lower] + 1 #1  if counter[approach_faster][approach_lower] is None else counter[approach_faster][approach_lower] + 1
    return counter


def readDissectionD4J():
    path = os.path.join("/Users/matias/develop/energy-research/greenRepairScripts/src/dissection_defects4j-bugs.json")
    f = open(path)
    djson = json.load(f)
    print(f.name)
    f.close()
    results = {}
    for bugData in djson:
        keyBug = "{}-{}".format(bugData["project"], bugData["bugId"])
        results[keyBug] = bugData

    return results


def readHard():
    result = {}

    with open("/Users/matias/develop/energy-research/greenRepairScripts/src/Hard_Defects4J.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            keyBugId = "{}-{}".format(row['Project'], row['DefectId'])
            result[keyBugId] = {}

            for k in row.keys():
                # print(row['Project'], row['DefectId'], row["TimeToFix"])

                result[keyBugId][k] = row[k]

    # print(reader)
    return result


if __name__ == '__main__':
    print("Traditional results")

    exportResults("../", "traditional_apr", addTest=True,
                  nameSet="traditional")

    print("LLM results")
    exportResults("../", "llm_based", addTest=False,
                  nameSet="LLM")
