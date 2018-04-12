import os
import ast
import csv
import argparse


def calculate_values(list_gold,list_comp) :
    set_gold=set(list_gold)
    set_comp=set(list_comp)
    #print set_gold
    #print set_comp
    TP=len(set_gold.intersection(set_comp))
    FP=len(set_comp.difference(set_gold))
    FN=len(set_gold.difference(set_comp))
    return [TP,FP,FN]


def calculate_metric(TP,FP,FN) :
    recall="NA"
    precision="NA"
    sum_precision_deno=TP+FP
    if sum_precision_deno!=0 :
        precision=TP/float(sum_precision_deno)
    sum_recall_deno=TP+FN
    if sum_recall_deno!=0 :
        recall=TP/float(sum_recall_deno)
    return (precision,recall)

def sep_keys(first_key,second_key,line,mydict):
    idx = line.find(first_key+":")
    if (idx == -1):
        return mydict
    line = line[idx:]
    if (second_key==""):
        block = line.strip()
    else:
        block = line.split(second_key+":")[0].strip()

    if block.endswith("|"):
        block = block[:-1]
    parts = block.split(":")

    key = parts[0].strip()
    value = parts[1].strip()
    mydict[key] = value
    return mydict

#Each file contains all the citations to a reference article. Therefore the keys in the dictionary for each file are the citing articles
#and each citing article then have a list of citation marker offsets
def load_dict(filename):
    
    header_fields = ['Citance Number', 'Reference Article','Citing Article','Citation Marker Offset','Citation Marker',
                     'Citation Offset','Citation Text','Reference Offset','Reference Text','Discourse Facet','Annotator']
    
    myfile=open(filename,"r")
    res = {}

    for line in myfile.readlines():
        line = line.strip()
        if line.strip()=="":
            continue
            
        mydict = {}
        for idx in range(0,len(header_fields)):
            if idx == (len(header_fields)-1):
                mydict = sep_keys(header_fields[idx],"",line,mydict)
            else:
                mydict = sep_keys(header_fields[idx],header_fields[idx+1],line,mydict)
        
        citing_article = mydict['Citing Article']

        if not mydict['Citation Marker Offset'].startswith("["):
            mydict['Citation Marker Offset'] = "[" + mydict['Citation Marker Offset']
        if not mydict['Citation Marker Offset'].endswith("]"):
            mydict['Citation Marker Offset'] = mydict['Citation Marker Offset'] + "]"
        marker_offset = mydict['Citation Marker Offset']
         
        if not mydict['Discourse Facet'].startswith("["):
            mydict['Discourse Facet'] = "[\'" + mydict['Discourse Facet'] + "\']"
        mydict['Discourse Facet'] = ast.literal_eval(mydict['Discourse Facet'])
        
        mydict['Reference Offset'] = ast.literal_eval(mydict['Reference Offset'])
        mydict['Citation Offset'] = ast.literal_eval(mydict['Citation Offset'])
        mydict['Citation Marker Offset'] = ast.literal_eval(mydict['Citation Marker Offset'])
        
        citing_article_dict = {}
        if citing_article in res:
            citing_article_dict = res[citing_article]
        
        citing_article_dict[marker_offset] = mydict
        res[citing_article] = citing_article_dict
    myfile.close()
    return res


def main():
    parser = argparse.ArgumentParser(description='Scisumm shared task evaluation ')
    parser.add_argument('--gold_folder',default="eval_data/Gold/Default/Task1/")
    parser.add_argument('--test_folder')
    args = parser.parse_args()
    print(args)
    
    #loading gold standard into dictionary
    dict_gold = {}
    for myfile in os.listdir(args.gold_folder):
        if myfile.startswith('.'):
            continue
        gold_filename=myfile.split(".")[0]
        dict_gold[gold_filename] = load_dict(args.gold_folder+myfile)
        
    #writing the results to this file
    csvfile=open('results_task1_last.csv', 'w') 
    fieldnames = ['System_Name','Filename','Precision_Task_1a','Recall_Task_1a','F1_Score_Task_1a','Precision_Task_1b','Recall_Task_1b','F1_Score_Task_1b']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    #reading results of different systsems and loading them into dictionary
    test_folder = args.test_folder
    for systems in os.listdir(test_folder):
        if systems!="Gold" and systems!="System3" :
            if systems.startswith('.'):
                continue
            if not os.path.isdir(os.path.join(test_folder,systems)):
                continue
            for runs in os.listdir(test_folder+systems):
                if runs.startswith('.'):
                    continue
                system_name= systems+"->"+runs
                print(system_name)

                dict_comp={}
                comp_file_path=test_folder+systems+"/"+runs+"/Task1/"
                for myfile in os.listdir(comp_file_path) :
                    if myfile.startswith('.'):
                        continue
                    comp_filename=myfile.split(".")[0]
                    #dict_comp=make_dict(comp_file_path+comp_filename+".annv3.txt",dict_comp)
                    dict_comp[comp_filename]= load_dict(comp_file_path+myfile)
                for files in dict_gold :

                    main_file_values=dict_gold[files]
                    comp_file_values=dict_comp[files]
                    [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[0,0,0]
                    #[TP_citation_marker,FP_citation_marker,FN_citation_marker]=[0,0,0]
                    #[TP_citation_offset,FP_citation_offset,FN_citation_offset]=[0,0,0]
                    [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[0,0,0]


                    for gold_values in main_file_values :
                        if gold_values in comp_file_values :
                            for gold_values_2 in main_file_values[gold_values] :
                                if gold_values_2 in comp_file_values[gold_values] :
                                        gold_value=main_file_values[gold_values][gold_values_2]
                                        comp_value=comp_file_values[gold_values][gold_values_2]
                                        old_value=TP_reference_offset        
                                        [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[x+y for x,y in zip([TP_reference_offset,FP_reference_offset,FN_reference_offset], calculate_values(gold_value["Reference Offset"],comp_value["Reference Offset"]))]
                                        if (TP_reference_offset-old_value)>=1:
                                            [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values(gold_value["Discourse Facet"],comp_value["Discourse Facet"]))]
                                        else :
                                            [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values(gold_value["Discourse Facet"],[]))]

                                else :
                                        print(gold_values_2,comp_file_values[gold_values],gold_values_2 in comp_file_values[gold_values] )
                                        gold_value=main_file_values[gold_values][gold_values_2]
                                        [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[x+y for x,y in zip([TP_reference_offset,FP_reference_offset,FN_reference_offset], calculate_values(gold_value["Reference Offset"],[]))]
                                        [TP_disourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values(gold_value["Discourse Facet"],[]))]
                                        print("2")   
                        else :
                            for gold_values_2 in main_file_values[gold_values] :
                                gold_value=main_file_values[gold_values][gold_values_2]
                                [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[x+y for x,y in zip([TP_reference_offset,FP_reference_offset,FN_reference_offset], calculate_values(gold_value["Reference Offset"],[]))]
                                [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values(gold_value["Discourse Facet"],[]))]
                                print("4")

                    for comp_values in comp_file_values:
                        if comp_values in main_file_values :
                            for comp_values_2 in comp_file_values[comp_values] :
                                if comp_values_2 not in main_file_values[comp_values] :
                                    comp_value=comp_file_values[comp_values][comp_values_2]
                                    [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[x+y for x,y in zip([TP_reference_offset,FP_reference_offset,FN_reference_offset], calculate_values([],comp_value["Reference Offset"]))]
                                    [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values([],comp_value["Discourse Facet"]))]
                                    print("1")

                        else :
                            for comp_values_2 in comp_file_values[comp_values] :
                                comp_value=comp_file_values[comp_values][comp_values_2]
                                [TP_reference_offset,FP_reference_offset,FN_reference_offset]=[x+y for x,y in zip([TP_reference_offset,FP_reference_offset,FN_reference_offset], calculate_values([],comp_value["Reference Offset"]))]
                                [TP_discourse_facet,FP_discourse_facet,FN_discourse_facet]=[x+y for x,y in zip([TP_discourse_facet,FP_discourse_facet,FN_discourse_facet], calculate_values([],comp_value["Discourse Facet"]))]
                                print("3")

                    (precision_discourse_facet,recall_discourse_facet)=calculate_metric(TP_discourse_facet,FP_discourse_facet,FN_discourse_facet)
                    if precision_discourse_facet!="NA" and recall_discourse_facet!="NA" :
                        if precision_discourse_facet+recall_discourse_facet!=0 :
                            f1_score_discourse_facet=2*precision_discourse_facet*recall_discourse_facet/float(precision_discourse_facet+recall_discourse_facet)
                        else :
                            f1_score_discourse_facet="NA"
                    else :
                        f1_score_discourse_facet="NA"
                        #(precision_citation_marker,recall_citation_marker)=calculate_metric(TP_citation_marker,FP_citation_marker,FN_citation_marker)
                        #(precision_citation_offset,recall_citation_offset)=calculate_metric(TP_citation_offset,FP_citation_offset,FN_citation_offset)
                    (precision_reference_offset,recall_reference_offset)=calculate_metric(TP_reference_offset,FP_reference_offset,FN_reference_offset)
                    if precision_reference_offset!="NA" and recall_reference_offset!="NA" :
                        if precision_reference_offset+recall_reference_offset!=0 :
                            f1_score_reference_offset=2*precision_reference_offset*recall_reference_offset/float(precision_reference_offset+recall_reference_offset)
                        else :
                            f1_score_reference_offset="NA"
                    else :
                        f1_score_reference_offset="NA"
                   # writer.writerow({'System_Name': systems, 'Method': runs, 'Filename' :files,'Precision_Task_1a': precision_reference_offset,'Recall_Task_1a': recall_reference_offset,'F1_Score_Task_1a': f1_score_reference_offset,'Precision_Task_1b': precision_discourse_facet,'Recall_Task_1b': recall_discourse_facet,'F1_Score_Task_1b': f1_score_discourse_facet})
                    writer.writerow({'System_Name': systems+"$"+runs, 'Filename' :files,'Precision_Task_1a': precision_reference_offset,'Recall_Task_1a': recall_reference_offset,'F1_Score_Task_1a': f1_score_reference_offset,'Precision_Task_1b': precision_discourse_facet,'Recall_Task_1b': recall_discourse_facet,'F1_Score_Task_1b': f1_score_discourse_facet})

    csvfile.close()

if __name__ == '__main__':
    main()


