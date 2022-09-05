import json
import statistics
import scipy
import os
'''
Given the energy  previously computed and summarized in energy_summary, it summarizes the results and outputs table for latex
'''

def exportResults(resultsFolder, execId, minNrExecutions = 2, allEnergyJoules = True):

	bugwithAssessmen = set()
	bugwithoutAssessmen = set()
	bugAppwithoutAssessmen = set()
	bugUnkAssessmen = set()

	pathEnergySummary = "{}/energy_summary/{}".format(resultsFolder, execId)
	pathTestEnergySummary = "{}/energy_test_suite_summary/{}".format(resultsFolder, execId)

	energyFirstPatch = {}
	energyTotalWithPatches = {}
	energyFirstCorrectPatch = {}
	executionTimeTotalWithPatches = {}

	allApproaches = set()

	withLessThanMinNumberExec = []

	missingTestEnergyInformation = []


	listWithPatchExecutionTime = []
	listWithPatchExecutionTimeFirstPatch = []
	listWithPatchEnergyTotal = []
	listWithEnergyFirstPatch = []
	pairsTimeEnergyPerTool = {}

	dataPerTool = {}


	## Read the bugs to consider
	pathFileAll = "/Users/matias/develop/post-overfitting/speedy_runner/scripts/allTestD4j.txt"

	file1 = open(pathFileAll, 'r')
	Lines = file1.readlines()
	file1.close()
	count = 0
	# Strips the newline character
	allBugsToConsider = []

	## Corresponds to all bugs that must not be considered in this experiment
	discardedBugsOutOfScope = []



	for line in Lines:
		count += 1
		allBugsToConsider.append(line.strip())

	for oneEnergyResult in os.listdir(pathEnergySummary):

		if ".DS_Store" == oneEnergyResult:
			continue

		f = open(os.path.join(pathEnergySummary, oneEnergyResult), "r")

		energyRes = json.loads(f.read())
		f.close()

		kid = energyRes["TOOL_BUG_ID"]
		kids = str(kid).strip().split("-")

		approach = kids[0]
		project =  kids[1]
		bugid =  kids[2]

		idbug = "{} {}".format(project, bugid)

		### We check the bugid is one of those we consider
		if idbug not in allBugsToConsider:
			#print("NOT IN {}: {}".format(idbug,allBugsToConsider ))
			discardedBugsOutOfScope.append(kid)
			continue


		keyBug = "{}-{}".format(project, bugid)

		#####
		## Retrieve consumption of test

		oneTestEnergyResult = "energy_test_summary_TestD4j-{}-{}.json".format(project, bugid)
		pathTestSummary = os.path.join(pathTestEnergySummary, oneTestEnergyResult)

		energyTestJules = None
		keyJoules = "Joules" if allEnergyJoules == True else "JoulesNormalized"


		if os.path.exists(pathTestSummary):
			f = open(pathTestSummary, "r")
			testEnergyRes = json.loads(f.read())
			f.close()
			#print("testEnergyRes", testEnergyRes)

			energyTestJules = testEnergyRes[keyJoules]["median"]

		else:
			missingTestEnergyInformation.append(keyBug)

		#Retrieve data from Bug

		totalEnergyJ = energyRes[keyJoules]["median"]
		totalEnergyJNormalized = energyRes["JoulesNormalized"]["median"]

		totalTime = energyRes["Time"]["median"]
		PowerAvg =  energyRes["PowerAvg"]["median"]
		nrExec  = energyRes["NrExecutions"]
		totalNrPatches = energyRes["NrPatches"]["median"]

		## We check the number of execution
		if int(nrExec) < minNrExecutions:
			withLessThanMinNumberExec.append(kid)
			continue

		firstPatchEnergyJ = None
		firstCorrectPatchEnergyJ = None
		firstPatchEnergyJNormalized = None
		firstCorrectPatchEnergyJNormalized = None
		allApproaches.add(approach)

		keyJoulesPerPatch = "Joules_Per_PatchMedian" if allEnergyJoules == True else "JoulesNormalized_Per_PatchMedian"

		if len(energyRes[keyJoulesPerPatch])>0:
			firstPatchEnergyJ = energyRes["Joules_Per_PatchMedian"][0]
			firstPatchEnergyJNormalized = energyRes["JoulesNormalized_Per_PatchMedian"][0]
			firstPatchExecutionTime = energyRes["ExecutionTime_Per_PatchMedian"][0]

		if len(energyRes["Correctness_Per_Patch"]) > 0:

			#### Check those with assessment
			#firstAssessment = energyRes["Correctness_Per_Patch"][0]
			#print("first", firstAssessment)
			#if firstAssessment == "na":
			#	bugwithoutAssessmen.add(keyBug)
			#	bugAppwithoutAssessmen.add(kid)
			#elif firstAssessment == "C" or firstAssessment == "I":
			#	bugwithAssessmen.add(keyBug)
			#else:
			#	bugUnkAssessmen.add(keyBug)
			## Retrieve assessment:

			for iAssess in range(0, len(energyRes["Correctness_Per_Patch"])):
				if energyRes["Correctness_Per_Patch"][iAssess] == "C":
					if iAssess < len(energyRes[keyJoulesPerPatch]):
						firstCorrectPatchEnergyJ = energyRes["Joules_Per_PatchMedian"][iAssess]
						firstCorrectPatchEnergyJNormalized =  energyRes["JoulesNormalized_Per_PatchMedian"][iAssess]
					break


		#print("-->", approach, keyBug,totalEnergyJ, totalTime, firstPatchEnergyJ, PowerAvg,nrExec,totalNrPatches  )
		### Store
		#### Init structures
		if keyBug not in executionTimeTotalWithPatches:
			energyFirstPatch[keyBug] = []
			energyTotalWithPatches[keyBug] = []
			executionTimeTotalWithPatches[keyBug] = []
			energyFirstCorrectPatch[keyBug]= []


		## TO CHECK
		if totalNrPatches > 0:
			energyTotalWithPatches[keyBug].append((approach, totalEnergyJ))
			executionTimeTotalWithPatches[keyBug].append((approach, totalTime))

		if firstCorrectPatchEnergyJ is not None:
			energyFirstCorrectPatch[keyBug].append((approach, firstCorrectPatchEnergyJ))

		if firstPatchEnergyJ is not None:
			energyFirstPatch[keyBug].append((approach, firstPatchEnergyJ))

			# Repaired and not repaired
			listWithPatchEnergyTotal.append(totalEnergyJ)
			listWithPatchExecutionTime.append(totalTime)
			listWithEnergyFirstPatch.append(firstPatchEnergyJ)
			listWithPatchExecutionTimeFirstPatch.append(firstPatchExecutionTime)

			if approach not in pairsTimeEnergyPerTool:
				pairsTimeEnergyPerTool[approach] = []
			pairsTimeEnergyPerTool[approach].append((totalTime, totalEnergyJ, firstPatchExecutionTime, firstPatchEnergyJ, keyBug ))

		## Now all
		if approach not in dataPerTool:
			dataPerTool[approach] = []

		#dataPerTool[approach].append(( totalEnergyJ, firstPatchEnergyJ, firstCorrectPatchEnergyJ, totalEnergyJNormalized,  energyTestJules,  keyBug))
		dataPerTool[approach].append({"totalEnergyJ":totalEnergyJ,
									  "totalEnergyJNormalized": totalEnergyJNormalized,
									  "firstPatchEnergyJ":  firstPatchEnergyJ,
									  "firstPatchEnergyJNormalized":  firstPatchEnergyJNormalized,
									  "firstCorrectPatchEnergyJ": firstCorrectPatchEnergyJ,
									  "firstCorrectPatchEnergyJNormalized": firstCorrectPatchEnergyJNormalized,

									  "energyTestJules": energyTestJules, "keyBug": keyBug})

	print("\n----Summary of Data--\n")

	withLessThanMinNumberExec = sorted(withLessThanMinNumberExec)

	print("\nWithout enough executions ({}) {}".format(len(withLessThanMinNumberExec), withLessThanMinNumberExec))

	## Check those not executed that are in the files to be executed.
	#missing = checkMissingToBeExecuted(withLessThanMinNumberExec, "/Users/matias/develop/post-overfitting/speedy_runner/scripts/")

#	print("Bugid to be considered without data ({}) {}".format(len(missing), sorted(missing)))


	print("Missing test information ", set(missingTestEnergyInformation))
	print("Not considered because out of scope ", sorted(discardedBugsOutOfScope))

	print("\nAll approaches considered ", allApproaches)

	print("\n----Results--------\n")


	############ RESULTS

	titleEnergyFirstPatch = "Comparison between approaches energy for First patch (X$>$Y means \# of times X is more efficient than Y)"
	print("\n***** Summary: " + titleEnergyFirstPatch)
	counterFasterFirstPatch = generateComparison(energyFirstPatch)
	#showCounter(counterFasterFirstPatch)
	printMatrics(allApproaches, counterFasterFirstPatch, caption=titleEnergyFirstPatch,
				 label="comparison:energy:firstpatch")



	######################

	## Print total energy
	titleTotalEnergy = "Comparison between approaches Total energy  (X$>$Y means \# of times X is more efficient than Y)"
	print("\n***** Summary " + titleTotalEnergy)
	counterTotalEnergy = generateComparison(energyTotalWithPatches)
	# showCounter(counterFasterTotalEnergy)
	printMatrics(allApproaches, counterTotalEnergy, titleTotalEnergy, "comparison:energy:total")

	######################

	titleExecutionTime = "Comparison between approaches Execution time (X$>$Y means \# of times X is more efficient than Y)"
	counterExecutionTimeTotalWithPatches = generateComparison(executionTimeTotalWithPatches)
	print("\n***** Summary " + titleExecutionTime)
	#showCounter(counterExecutionTimeTotalWithPatches)

	printMatrics(allApproaches, counterExecutionTimeTotalWithPatches, caption=titleExecutionTime,
				 label="comparison:exectime", showDetail=True)


	####

	titleEnergyFirstCorrectPatch = "Comparison between approaches energy for First Correct patch (X$>$Y means \# of times X is more efficient than Y)"
	print("\n***** Summary: " + titleEnergyFirstPatch)
	counterFasterFirstCorrectPatch = generateComparison(energyFirstCorrectPatch)
	## temporal: to put zeros
	#for a in allApproaches:
	#	for b in allApproaches:
	#		counterFasterFirstCorrectPatch[a][b] = []

	## End temporal
	#https://datagy.io/python-pearson-correlation/
	#showCounter(counterFasterFirstPatch)
	printMatrics(allApproaches, counterFasterFirstCorrectPatch, caption=titleEnergyFirstCorrectPatch,
				 label="comparison:energy:firstcorrectpatch", addOverTotal=True)


	###########
	print("correlation time-energy\n")
	printCorrelation(allApproaches, listWithEnergyFirstPatch, listWithPatchEnergyTotal,  listWithPatchExecutionTimeFirstPatch, listWithPatchExecutionTime,
					 pairsTimeEnergyPerTool)



	print("Main Table\n")

	printMainTableValueMetrics(allApproaches, dataPerTool, printToTalEnergy=False)

	computeDifferences(allApproaches, dataPerTool)

	printTableMannWPvalues(allApproaches, dataPerTool, caption="Comparison of the distribution $Energy_{first\_patch}$ using the Mann-Whitney test. Cells show $p-values$. Cells with $p < 0.005$ (that is, rejection of $H_0$) are colored black).", label="mannwhitneyutest")

	## Assessment:
	print("With {} {} ".format(len(bugwithAssessmen), sorted(bugwithAssessmen)))
	print("Without {} {} ".format(len(bugwithoutAssessmen), sorted(bugwithoutAssessmen)))
	print("Missing {} {} ".format(len(bugAppwithoutAssessmen), sorted(bugAppwithoutAssessmen)))
	print("Unk {} {} ".format(len(bugUnkAssessmen), bugUnkAssessmen))
	print("Intersection {} ".format( sorted(bugwithAssessmen.intersection(bugwithoutAssessmen))))


def computeDifferences(allApproaches, dataPerTool):

	#energyFirstX = dataPerTool[approachX]["firstPatchEnergyJ"]
	#energyFirstY = dataPerTool[approachY]["firstPatchEnergyJ"]
	allEnergyFirst = {}
	for approach in allApproaches:
			allEnergyFirst[approach] = []
			#print(dataPerTool[approach])
			for bug in dataPerTool[approach]:
				value = bug["firstPatchEnergyJ"]
				if  value is not None:
					allEnergyFirst[approach].append(value)


	for approachX in dataPerTool:
		timesRejectHo = 0
		timesAcceptH0 = 0

		listRejected = []
		listAccepted = []


		for approachY in dataPerTool:


			if approachX is not approachY:

				#print(approachX, approachY)
				#print(len(allEnergyFirst[approachX]), len(allEnergyFirst[approachY]))
				resultMannW = scipy.stats.mannwhitneyu(allEnergyFirst[approachX], allEnergyFirst[approachY])
				#print(resultMannW.pvalue)

				if resultMannW.pvalue  < 0.05:
					#print("Reject null")
					timesRejectHo+=1

				else:
					timesAcceptH0+=1

		print("tool {} times reject (dif dist) {} times accept (sim dist) {}".format(approachX, timesRejectHo, timesAcceptH0))


def printMainTableValueMetrics(allApproaches,
							   dataPerTool, printToTalEnergy = False ):

	#[approach].append((totalTime, totalEnergyJ, firstPatchEnergyJ, keyBug)

	# print("Number of samples {}".format(len(listAllExecutionTime)))

	totalD4J1_2 = 395

	print("\\begin{table*}[]")
	print("\centering")
	print("\\begin{tabular}{" + "| l | r| r||"+
		  ("  r|  r| r  ||" if printToTalEnergy else "")
								+ " r|  r| r  || r|  r| r  || r|  " + "}")
	print("\hline")
	# p
	#print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
	#print("&  &{First patch} & {Total execution}\\\\")
	#print("\cline{2-5}")

	print("&  \multicolumn{2}{c}{Patches} & " +
		  ( "  \multicolumn{3}{|c||}{$Energy_{Total}$} &"  if printToTalEnergy else "")
		  +
		  "   \multicolumn{3}{|c||}{$Energy_{first\_patch}$}  &  \multicolumn{3}{|c|| }{$Energy_{correct\_patch}$} & \multirow{2}{*}{CTA}\\\\")


	print("\\cline{2-12}" if  printToTalEnergy else  "\\cline{2-9}")



	print("Approach & \#Plausible &  \#Correct &  "
		  +  ("Gross (J) &  Net (J) &  NormTest  &" if printToTalEnergy else "")
		  + " Gross (J) &  Net (J) &  NormTest  & Gross (J) &  Net (J) &  NormTest  & \\\\")
	print("\hline")
	import numpy as np
	import scipy.stats

	# print("All ", resultA)

	#print("\hdashline")
	## by tool:
	for a in sorted(allApproaches):
		values = dataPerTool[a]

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


		for v in values:

			# dataPerTool[approach].append((totalEnergyJ, firstPatchEnergyJ, firstCorrectPatchEnergyJ, keyBug))

			#dataPerTool[approach].append({"totalEnergyJ":totalEnergyJ, "firstPatchEnergyJ":  firstPatchEnergyJ, "firstCorrectPatchEnergyJ": firstCorrectPatchEnergyJ, "totalEnergyJNormalized": totalEnergyJNormalized,
			#						  "energyTestJules": energyTestJules, "keyBug": keyBug})

			listEnergAll.append(v["totalEnergyJ"])
			listEnerAllNorm.append(v["totalEnergyJNormalized"])
			listEnergRelative.append(v["totalEnergyJ"] / v["energyTestJules"] )


			if v["firstPatchEnergyJ"] is not None:
				listEnergFirst.append(v["firstPatchEnergyJ"])
				listEnergFirstRelative.append(v["firstPatchEnergyJ"] / v["energyTestJules"])
				listEnergFirstNorm.append(v["firstPatchEnergyJNormalized"])


			if v["firstCorrectPatchEnergyJ"] is not None:
				listEnergCorrectFirst.append(v["firstCorrectPatchEnergyJ"])
				listEnergCorrectFirstRelative.append(v["firstCorrectPatchEnergyJ"]/ v["energyTestJules"])
				listEnergCorrectFirstNorm.append(v["firstCorrectPatchEnergyJNormalized"])

			listBugIds.append(v["keyBug"])

		listBugIds = sorted(listBugIds)
		#print("-- {} Number of samples {}: bugsid {}".format(a, len(listBugIds), listBugIds ))

		medianTotalE = statistics.median(listEnergAll)
		stdTotalE = statistics.stdev(listEnergAll)
		medianEnergyAllNorm = statistics.median(listEnerAllNorm)
		medianTotalEnergyRelative2Test = statistics.median(listEnergRelative)

		medianFirst  = statistics.median(listEnergFirst)
		stdFirst = statistics.stdev(listEnergFirst)
		medianFirstRelative = statistics.median(listEnergFirstRelative)
		medianFirstNorm = statistics.median(listEnergFirstNorm)

		## Count plausibles
		plausibles = len(listEnergFirst)
		corrects = len(listEnergCorrectFirst)

		meanCorrect = "-"
		meanCorrectRelative = "-"

		if len(listEnergCorrectFirst) > 0:
			meanCorrect = statistics.median(listEnergCorrectFirst)
			meanCorrectRelative = statistics.median(listEnergCorrectFirstRelative)
			meanCorrectNorm = statistics.median(listEnergCorrectFirstNorm)
			if len(listEnergCorrectFirst) > 2:
				stdCorrect = statistics.stdev(listEnergCorrectFirst)

		accuracy = (corrects / totalD4J1_2 )
		score = accuracy / medianTotalE

		cta = medianTotalE / (accuracy  * 10)
		if printToTalEnergy:
			print("{} &  {} & {} " 
				  " & {:0.0f} &  {:0.0f} &  {:0.2f} "
				   " & {:0.0f} &  {:0.0f} &  {:0.2f} "
				  " & {:0.0f} &  {:0.0f} &  {:0.2f} "
				  "   & {:0.0f} \\\\".format(a, plausibles, corrects,
																								  medianTotalE, medianEnergyAllNorm, medianTotalEnergyRelative2Test,
																								 medianFirst, medianFirstNorm, medianFirstRelative,
																									   meanCorrect,meanCorrectNorm, meanCorrectRelative,
																									   cta ))
		else:
			print("{} &  {} & {} "
				   " & {:0.0f} &  {:0.0f} &  {:0.2f} "
					" & {:0.0f} &  {:0.0f} &  {:0.2f} "
					"   & {:0.0f} \\\\".format(a, plausibles, corrects,
											 #  medianTotalE, medianEnergyAllNorm, medianTotalEnergyRelative2Test,
											   medianFirst, medianFirstNorm, medianFirstRelative,
											   meanCorrect, meanCorrectNorm, meanCorrectRelative,
											   cta))


	print("\hline")
	print("\end{tabular}")
	print("\caption{"+" }")
	print("\label{tab:"
		  + "resultsMetrics" + "}")
	print("\end{table*}")
	print("\n\n")



def printCorrelation(allApproaches, listAllEnergyFirstPatch, listAllEnergyTotal, listAllExecutionTimeFirstPatch,  listAllExecutionTime,
					 pairsTimeEnergyPerTool):
	# print("Number of samples {}".format(len(listAllExecutionTime)))
	print("\\begin{table}[]")
	print("\centering")
	print("\\begin{tabular}{" + "| l | r| r | r | " + "}")
	print("\hline")
	# p
	#print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
	print("&  &{First patch} & {Total execution}\\\\")
	print("\cline{3-4}")
	print("Tool &  \#Repaired  & R pearson &     R pearson  \\\\")
	print("\hline")
	import numpy as np
	import scipy.stats
	resultF = scipy.stats.pearsonr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
	resultA = scipy.stats.pearsonr(listAllExecutionTime, listAllEnergyTotal)
	# print("First ", resultF)
	# print("All ", resultA)
	print("All&  {} &   {:0.2f}  & {:0.2f}   \\\\".format(len(listAllExecutionTime),  resultF[0],  resultA[0]))
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
			#totalTime, totalEnergyJ, firstPatchExecutionTime, firstPatchEnergyJ
			listTimes.append(v[0])
			listEnergAll.append(v[1])
			listTimesFirst.append(v[2])
			listEnergFirst.append(v[3])
			listBugIds.append(v[4])

		listBugIds = sorted(listBugIds)
		#print("-- {} Number of samples {}: bugsid {}".format(a, len(listBugIds), listBugIds ))
		#print("-- {} Number of samples {}".format(a, len(listTimes)))
		#https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
		resultF = scipy.stats.pearsonr(listTimesFirst, listEnergFirst)
		resultA = scipy.stats.pearsonr(listTimes, listEnergAll) # , alternative='greater'
		#	print("First ", resultF)
		#	print("All ", resultA)
		print("{} & {} &  {:0.2f} & {:0.2f}  \\\\".format(a, len(listTimes), resultF[0],  resultA[0]))

	print("\hline")
	print("\end{tabular}")
	print("\caption{"
		  + "Pearson correlation between execution time and energy. The first column computes both metrics until the first patch is found, the second considers the energy and time for the complete execution." + "}")
	print("\label{tab:"
		  + "correlationEnergyTime" + "}")
	print("\end{table}")
	print("\n\n")



def printCorrelationPvalue(allApproaches, listAllEnergyFirstPatch, listAllEnergyTotal, listAllExecutionTimeFirstPatch,  listAllExecutionTime,
					 pairsTimeEnergyPerTool):
	# print("Number of samples {}".format(len(listAllExecutionTime)))
	print("\\begin{table}[]")
	print("\centering")
	print("\\begin{tabular}{" + "| l | r | r | r | r | " + "}")
	print("\hline")
	# p
	print("& \multicolumn{2}{c|}{First patch} & \multicolumn{2}{c|}{Total execution}\\\\")
	print("\cline{2-5}")
	print("Tool & R pearson &  P-value &   R pearson &  P-value \\\\")
	print("\hline")
	import numpy as np
	import scipy.stats
	resultF = scipy.stats.pearsonr(listAllExecutionTimeFirstPatch, listAllEnergyFirstPatch)
	resultA = scipy.stats.pearsonr(listAllExecutionTime, listAllEnergyTotal)
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
			#totalTime, totalEnergyJ, firstPatchExecutionTime, firstPatchEnergyJ
			listTimes.append(v[0])
			listEnergAll.append(v[1])
			listTimesFirst.append(v[2])
			listEnergFirst.append(v[3])
			listBugIds.append(v[4])

		print("-- {} Number of samples {}: bugsid {}".format(a, len(listTimes), listBugIds ))
		#https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
		resultF = scipy.stats.pearsonr(listTimesFirst, listEnergFirst)
		resultA = scipy.stats.pearsonr(listTimes, listEnergAll) # , alternative='greater'
		#	print("First ", resultF)
		#	print("All ", resultA)
		print("{} & {:0.2f} & {:0.5f} & {:0.2f} & {:0.5f} \\\\".format(a, resultF[0], resultF[1], resultA[0], resultA[1]))

	print("\hline")
	print("\end{tabular}")
	print("\caption{"
		  + "Pearson correlation between execution time and energy. The first column computes both metrics until the first patch found, the second considers the energy and time for the complete execution." + "}")
	print("\label{tab:"
		  + "correlationEnergyTime" + "}")
	print("\end{table}")
	print("\n\n")




'''
Given the energy  previously computed, it summarizes the results and outputs table for latex
This is computed from the energy files, not from the energy summary
TO BE DEPRECATED
'''
def deprecated_analyzeStoredEnergy(resultsFolder =""):
	pathLog = "{}/energy/".format(resultsFolder)

	energyFirstPatch = {}
	energyTotalWithPatches = {}
	executionTimeTotalWithPatches = {}

	allApproaches = set()

	for oneEnergyResult in os.listdir(pathLog):

		if ".DS_Store" == oneEnergyResult:
			continue

		f = open(os.path.join(pathLog, oneEnergyResult), "r")

		energyRes = json.loads(f.read())
		f.close()

		project = energyRes["project"]
		bugid = energyRes["bugid"]
		approach  = energyRes["approach"]
		allApproaches.add(approach)

		keyBug = "{}-{}".format(project, bugid)

		totalEnergyJ = energyRes["energyTotal"]["joules"]
		totalEnergyWh = energyRes["energyTotal"]["Wh"]
		totalTime = energyRes["energyTotal"]["timeExecution"]


		## First Patch
		if len(energyRes["energyPerPatch"]) > 0:
			firstPatchEnergyJ = energyRes["energyPerPatch"][0]["joules"]
			firstPatchEnergyW = energyRes["energyPerPatch"][0]["joules"]

			if keyBug not in energyFirstPatch:
				energyFirstPatch[keyBug] = []
				energyTotalWithPatches[keyBug] = []
				executionTimeTotalWithPatches[keyBug] = []
			energyFirstPatch[keyBug].append((approach, firstPatchEnergyJ))
			energyTotalWithPatches[keyBug].append((approach, totalEnergyJ))
			executionTimeTotalWithPatches[keyBug].append((approach, totalTime))

	print("All approaches", allApproaches)

	## Print energy first

#	print("energyFirstPatch {}".format(energyFirstPatch))




def printMatrics(allApproach, count, caption ="TO BE PUT" , label = "lab",showDetail = False, colored = True, addOverTotal = False ):
	print("\n\n")

	print("\\begin{table*}[]")
	print("\centering")


	#print("{ | l |}")


	aligheader="| l | "

	bestApproaches = {}
	participationsApproaches = {}

	allApproach = list(allApproach)
	allApproach.sort()
	for ap in allApproach:
		aligheader+=" c |"
		bestApproaches[ap] = 0
		participationsApproaches[ap] = 0

	print("\\begin{tabular}{"+aligheader+"}")
	#print(aligheader)
	print("\hline")
	firstrow = "&"
	for x in range(0, len(allApproach)):
		firstrow += " {} &".format(allApproach[x])

	firstrow = (firstrow[0:len(firstrow) - 1]) + "\\\\"
	print(firstrow)
	print("\hline")
	for y in range(0, len(allApproach)):
		approachY = allApproach[y]
		rowS=approachY+ " & "
		for x in range(0, len(allApproach)):

			approachX = allApproach[x]
			if approachX == approachY:
				row = "-"
			elif approachX in count and approachY in  count[approachX]:
				#row = "{}-{}".format(len(count[approachX][approachY]) ,count[approachX][approachY] )

				otherRound = 0
				if approachY in count and approachX in count[approachY]:
					otherRound = len(count[approachY][approachX])

				bestCurrent = len(count[approachX][approachY])
				if count[approachX][approachY] != 0:
					participationsApproaches[approachX] = participationsApproaches[approachX] + 1

				if bestCurrent != 0:
					percentage = (bestCurrent / (bestCurrent + otherRound))*100

				else:
					percentage = 0


				if percentage > 50:
					bestApproaches[approachX] = bestApproaches[approachX] + 1

				if colored:

					if addOverTotal:
						row = " \cca{"+ "{:0.0f}".format( percentage) + "}\%"+ " ({}/{}) ".format( bestCurrent, (bestCurrent + otherRound)) + (str(count[approachX][approachY]) if showDetail else "")
					else:
						row = " \cca{" + "{:0.0f}".format(percentage) + "}\%" + " ({}) ".format(bestCurrent) + (str(count[approachX][approachY]) if showDetail else "")



				else:
					row = "{} ({:0.2f}\%) ".format(bestCurrent, percentage)  +   (str(count[approachX][approachY])  if showDetail else "")
			else:
				if approachX in count and not approachY in count[approachX] and  approachY in count and  approachX in count[approachY]:
					otherRound = len(count[approachY][approachX])
					row = "0/{}".format(otherRound)
				else:

					row = 0
			rowS+=" {} &".format(row)

		rowS = (rowS[0:len(rowS)-1]) + "\\\\ \\hline"
		print(rowS)

	summaryRow = "\#comp $>$50\% &"
	print("\hline")
	for ap in allApproach:
		if participationsApproaches[ap] > 0:
			percBest = (bestApproaches[ap] / participationsApproaches[ap])*100
			summaryRow +=  "{} ({:0.1f}\%) ".format(bestApproaches[ap], percBest) + " &"
		else:
			summaryRow += "0 "+ " &"

	summaryRow = (summaryRow[0:len(summaryRow) - 1]) + "\\\\"
	print(summaryRow)

	print("\hline")
	print("\end{tabular}")
	print("\caption{"
		  +caption+ "}")
	print("\label{tab:"
		 + label+ "}")
	print("\end{table*}")
	print("\n\n")



def printTableMannWPvalues(allApproach, dataPerTool, caption ="TO BE PUT" , label = "lab",showDetail = False, colored = True, addOverTotal = False ):
	print("\n\n")

	allEnergyFirst = {}
	for approach in allApproach:
		allEnergyFirst[approach] = []
		# print(dataPerTool[approach])
		for bug in dataPerTool[approach]:
			value = bug["firstPatchEnergyJ"]
			if value is not None:
				allEnergyFirst[approach].append(value)


	print("\\begin{table*}[]")
	print("\centering")
	print("\tiny")


	#print("{ | l |}")


	aligheader="| l | "

	bestApproaches = {}
	participationsApproaches = {}

	allApproach = list(allApproach)
	allApproach.sort()
	for ap in allApproach:
		aligheader+=" c |"
		bestApproaches[ap] = 0
		participationsApproaches[ap] = 0

	print("\\begin{tabular}{"+aligheader+"}")
	#print(aligheader)
	print("\hline")
	firstrow = "&"
	for x in range(0, len(allApproach)):
		firstrow +=  "\rotatebox{90}{"+ " {} &".format(allApproach[x]) + "}"

	firstrow = (firstrow[0:len(firstrow) - 1]) + "\\\\"
	print(firstrow)
	print("\hline")
	for y in range(0, len(allApproach)):
		approachY = allApproach[y]
		rowS=approachY+ " & "

		timesRejectHo = 0
		timesAcceptH0 = 0

		listRejected = []
		listAccepted = []

		for x in range(0, len(allApproach)):

			approachX = allApproach[x]
			if approachX == approachY:
				row = "-"
			else:


				resultMannW = scipy.stats.mannwhitneyu(allEnergyFirst[approachX], allEnergyFirst[approachY])

				if resultMannW.pvalue < 0.05:
					# print("Reject null")
					timesRejectHo += 1
					if resultMannW.pvalue is 0:
						row = "\cpv{" + "0" + "}"
					#elif resultMannW.pvalue < 0.01:
					#	row = "\cpv{" + "$<$0.01" + "}"
					else:
						row = "\cpv{"+ "{:0.2f}".format(resultMannW.pvalue)+"}"
				else:
					timesAcceptH0 += 1
					row =  "{:0.2f}".format(resultMannW.pvalue)




			rowS+=" {} &".format(row)

		rowS = (rowS[0:len(rowS)-1]) + "\\\\ \\hline"
		print(rowS)

	if False:
		summaryRow = "\#comp $>$50\% &"
		print("\hline")
		for ap in allApproach:
			if participationsApproaches[ap] > 0:
				percBest = (bestApproaches[ap] / participationsApproaches[ap])*100
				summaryRow +=  "{} ({:0.1f}\%) ".format(bestApproaches[ap], percBest) + " &"
			else:
				summaryRow += "0 "+ " &"

		summaryRow = (summaryRow[0:len(summaryRow) - 1]) + "\\\\"
		print(summaryRow)

	print("\hline")
	print("\end{tabular}")
	print("\caption{"
		  +caption+ "}")
	print("\label{tab:"
		 + label+ "}")
	print("\end{table*}")
	print("\n\n")





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

		#print("Sorted {}: {}".format(aBugId,energyApproachesForBugid ))

		if len(energyApproachesForBugid) > 1:

			for iApproach in range(0, len(energyApproachesForBugid)):

				for iAnother in range(iApproach + 1, len(energyApproachesForBugid)):
					approach_faster = energyApproachesForBugid[iApproach][0]
					value_faster =  energyApproachesForBugid[iApproach][1]
					approach_lower = energyApproachesForBugid[iAnother][0]
					value_lower = energyApproachesForBugid[iAnother][1]
					l = "{} > {}".format(approach_faster, approach_lower)
					#counter[l] = counter.get(l, 0) + 1
					if approach_faster not in counter:
						counter[approach_faster] = {}

					if approach_lower not in counter[approach_faster]:
						#counter[approach_faster][approach_lower] = 0
						counter[approach_faster][approach_lower] = []

					counter[approach_faster][approach_lower].append((aBugId, value_faster, value_lower  )) #counter[approach_faster][approach_lower] + 1 #1  if counter[approach_faster][approach_lower] is None else counter[approach_faster][approach_lower] + 1
	return counter

