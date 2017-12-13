#!/usr/bin/python
#-*- coding: iso-8859-1 -*-

## From SNP genotypes to Crimap format
## Eric Normandeau 2009 11 17 - 2010 02 05

## This version can prepare SNP and microsat genotypes for crimap software


## Todo
##
## - Test plausibility of child genomes
##   a) done
##   b) done
##   c) Add *** before impossible genome
##   d) done
##   e) Print errors to output error text file


##########################
## User input (filenames)

INPUT_FILE = "genotype_data.txt"
OUTPUT_FILE = "_output_crimap_format.txt"
OUTPUT_CODE = "_output_crimap_code.txt"
OUTPUT_ERRORS = "_output_crimap_errors.txt"


##################
## Import modules

import string
import copy
import math


########################
## Function definitions

def readfile(path):
    """Read file and return a list containing the file lines"""
    out = []
    file = open(path, "r")
    for line in file:
        out.append(line.rstrip().split("\t"))
    file.close()
    return out

def writefile(var, path):
    """Write lines from the first dimension of structuring of an object"""
    file = open(path, "w")
    for line in var:
        file.write(line)
    file.close()

def locus_parse(locus):
    """Parse the allel information at one locus in one individual in 2 allels"""
    allels = None
    if locus == "0":
        allels = [0, 0]
    elif len(locus) == 2 and locus[0] in "ACGT" and locus[1] in "ACGT":
        allels = [locus[0], locus[1]]
    elif len(locus.split("_")) == 2:
        allels = locus.split("_")
    else:
        print locus, type(locus)
        print "Error in genotype format. Please verify your data"
    return allels

def allel_dict(allels):
    allels.remove(0)
    SNP = True
    for allel in allels:
        if allel not in "ACGT":
            SNP = False
    if SNP == True:
        dict = {0:0, "A":1, "C":2, "G":3, "T":4}
    else:
        dict = {0:0}
        allel_counter = 1
        for allel in allels:
            dict[allel] = allel_counter
            allel_counter += 1
    return dict


#########################
## Parsing genotype file

genotype_data = readfile(INPUT_FILE)
loci_names = genotype_data[0][3:]
individuals = genotype_data[1:]


####################################################################
## Pass through data to establish possible genotypes for each locus

loci_allel_lists = []

for locus in xrange(3, len(genotype_data[0])):
    loci_allel_lists.append([])
    for individual in individuals:
        allels = locus_parse(individual[locus])
        loci_allel_lists[-1].append(allels)

unique_loci_lists = []

for locus in loci_allel_lists:
    unique_loci_lists.append([])
    for genotype in locus:
        for allel in genotype:
            if allel not in unique_loci_lists[-1]:
                unique_loci_lists[-1].append(allel)
    unique_loci_lists[-1] = sorted(unique_loci_lists[-1])

loci_allel_dicts = []

for loci in unique_loci_lists:
    loci_allel_dicts.append(allel_dict(loci))


##############################
## Write loci codes to a file

output_dict = [str(sorted(dict.items())) + "\n" for dict in loci_allel_dicts]
writefile(output_dict, OUTPUT_CODE)


########################
## Encode genotype data 

individuals_coded = []

for i, individual in enumerate(individuals):
    individuals_coded.append([])
    individuals_coded[-1] += individual[0:3]
    for j, locus in enumerate(individual[3:]):
        allels = locus_parse(locus)
        for allel in allels:
            code = loci_allel_dicts[j][allel]
            individuals_coded[-1] += str(code)


##################################
## Test errors in child genotypes

errors = []

for i in xrange(len(individuals_coded)):
    for j in xrange(len(individuals_coded[i][3:]) / 2):
        parent_allels = [ind[3:][(2*j):(2*j+2)] 
                         for ind in individuals_coded if ind[1] == "1"]
        ind_allels = individuals_coded[i][3:][(2*j):(2*j+2)]
        all_parent_allels = list(set(parent_allels[0] + parent_allels[1]))
        allels_parent_1 = list(set(parent_allels[0]))
        allels_parent_2 = list(set(parent_allels[1]))
        for all in ind_allels:
            if all != "0" and all not in all_parent_allels:
#                print loci_names[j] + " individual: " + str(i + 1) + \
#                      " Achtung! Offspring allel not found in parents"
                errors.append("Err_AllNotPar_:\t" + "individual: " + str(i + 1) + "\t" + loci_names[j] + "\n")
                ind_allels[0] += "***"
                ind_allels[1] += "***"
        if ind_allels == ["0", "0"] and \
            (allels[0] not in allels_parent_1 or \
            allels[1] not in allels_parent_2) \
            and (allels[1] not in allels_parent_1 or \
            allels[0] not in allels_parent_2):
#            print loci_names[j] + " individual: " + str(i + 1) + \
#                  " Achtung! Both offspring allels come from the same parent"
            errors.append("Err_AllSamePar:\t" + "individual: " + str(i + 1) + "\t" + loci_names[j] + "\n")

"""

Write those errors to an output error text file
Add *ErrorCode* before the bad allel(s)

"""

errors = sorted([str("%08i" % int(err.split()[2])) + " " + err for err in errors])

errors = [" ".join(err.split()[1:]) + "\n" for err in errors]

writefile(errors, OUTPUT_ERRORS)




#########################################
## Building output data in crimap format

data_crimap = []

nb_markers = len(individuals[0][3:])
nb_F0 = 4  ## Number of grand-parents
nb_F1 = 2  ## Number of parents
nb_F2 = len(individuals_coded) - nb_F0 - nb_F1
nb_print_groups = int(math.ceil(nb_F2/54.))

data_crimap.append(str(nb_print_groups))
data_crimap.append(str(nb_markers))
data_crimap.append(loci_names)

individuals_F0 = [[ind[0]] + ["0", "0"] + ind[2:] 
                   for ind in individuals_coded if ind[1] == "0"]
individuals_F1 = [[ind[0]] + ["0", "0"] + ind[2:] 
                   for ind in individuals_coded if ind[1] == "1"]
individuals_F2 = [[ind[0]] + ["1", "2"] + ind[2:] 
                   for ind in individuals_coded if ind[1] == "2"]


###############################
## Writing data in output file

fam_number = 1

while individuals_F2:
    individuals_F2_temp = individuals_F2[0:44]
    individuals_F2 = individuals_F2[44:]
    data_crimap.append("")
    data_crimap.append(str("fam%03i" % fam_number))
    data_crimap.append(str(len(individuals_F2_temp) + len(individuals_F0) + \
                           len(individuals_F1)))
    for ind in individuals_F0:
        data_crimap.append(ind[0:4])
        data_crimap.append(ind[4:])
    for ind in individuals_F1:
        data_crimap.append(ind[0:4])
        data_crimap.append(ind[4:])
    for ind in individuals_F2_temp:
        data_crimap.append(ind[0:4])
        data_crimap.append(ind[4:])
    fam_number += 1


##################################
## Line formating for file output

output = ["\t".join(line) + "\n"  if type(line) == list else line + "\n" 
          for line in data_crimap]

writefile(output, OUTPUT_FILE)
