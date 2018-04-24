import ast
import xml.etree.ElementTree as ET
import os
import argparse
from collections import Counter
from nltk.tokenize import wordpunct_tokenize
from nltk.corpus import stopwords


class system_variables:
    header_fields = ['Citance Number', 'Reference Article','Citing Article','Citation Marker Offset','Citation Marker',
                     'Citation Offset','Citation Text','Reference Offset','Reference Text','Discourse Facet','Annotator']

    header_fields_to_keep_from_gold = ['Citance Number', 'Reference Article','Citing Article','Citation Marker Offset','Citation Marker',
                                   'Citation Offset','Citation Text']

    header_fields_for_blank_initialization = ['Reference Offset','Reference Text','Discourse Facet','Annotator']

    stoplist = stopwords.words("english") + ", \" : ' . ; ! ?".split()

    tok = wordpunct_tokenize


class Section:
    def __init__(self,xml_string):
        xml_string = xml_string.strip()
        if xml_string == "<ABSTRACT>":
            self.title = 'Abstract'
            self.section_number = 0
        else:
            xml_string = xml_string + "</SECTION>"
            element = ET.fromstring(xml_string)
            self.title = element.attrib["title"]
            try:
                self.section_number = int(element.attrib["number"])
            except:
                self.section_number = -1 #Unnumbered sections

class Sentence:
    def __init__(self,xml_string,section_list):
        element = ET.fromstring(xml_string)
        self.xml_original = xml_string
        self.text = element.text
        if len(section_list) > 0:
            self.section_number = section_list[-1].section_number
            try:
                self.sentence_idx_in_section = int(element.attrib['ssid'])
            except:
                self.sentence_idx_in_section = -1
            try:
                self.section_idx_in_article = int(element.attrib['sid'])
            except:
                self.section_idx_in_article = -1
        else:
            self.section_number = -1 #There are sentences right under <PAPER>, before <ABSTRACT>, possible spare titles
            self.sentence_idx_in_section = -1
            self.section_idx_in_article = int(element.attrib['sid'])

    def __str__(self):
        return self.xml_original

class Article:
    def __init__(self,file_name):
        self.file_name = file_name
        self.sections = []
        self.sentences = []
    
    def __str__(self):
        return "File %s with %d sections and %d sentences" % (self.file_name,len(self.sections),len(self.sentences))

class Entry(dict): #Each entry from the annotation files
    def __init__(self):
        super(Entry, self).__init__() #call the dictionary constructor

    def featurize(self):
        fv = {} #feature_vector
        cit = set(system_variables.tok(self['Citation Text']))
        ref = set(system_variables.tok(self['Reference Text']))
        for x in cit:
            fv["c_"+x] = 1
        for x in ref:
            fv["r_"+x] = 1
        fv["intersection"] = len(cit.intersection(ref))
        fv["len_cit_off"] = self["Citation Offset"].count(",")
        fv["len_ref_off"] = self["Reference Offset"].count(",")
        return fv

    def get_ground_truth(self):
        return len(self['Reference Offset'])

    def sentence_scoring_baseline(self):
        sentence_scorer = Counter()

        for reference_sentence in self['Reference Article Content'].sentences:
            sentence_scorer[reference_sentence]=self.score_sentence(reference_sentence)
        highest_scoring_sentence,score = sentence_scorer.most_common(1)[0]
        pred_offset = "['"+str(highest_scoring_sentence.section_idx_in_article)+"']"
        pred_reference_text = highest_scoring_sentence.xml_original
        return pred_offset,pred_reference_text

    def score_sentence(self,candidate_reference_sentence):
        """
        This function gives an integer score (the size of the intersection of the sets of unigrams between Citation
        and candidate reference). It is just a baseline function used as placeholder
        """
        cit_sentence_list = self['Citation Text Content']
        cit_words = []
        for sentence in cit_sentence_list:
            cit_words.extend(wordpunct_tokenize(sentence.text))
        ref_words = wordpunct_tokenize(candidate_reference_sentence.text)
        cit_words = set(cit_words)
        ref_words = set(ref_words)
        return len(cit_words.intersection(ref_words))

    def out_file_format(self):
        out=[]
        for k in system_variables.header_fields:
            out.append(k+": "+self[k])
        outline = " | ".join(out) + "\n"
        return outline


def read_XML(infile_path):
    file_name = infile_path.split("/")[-1]
    article = Article(file_name)

    for line in open(infile_path).readlines():
        line = line.strip()
        if line.startswith("<ABSTRACT"):
            article.sections.append(Section(line))
        elif line.startswith("</ABSTRACT"):
            pass
        elif line.startswith("<SECTION"):
            article.sections.append(Section(line))
        elif line.startswith("</SECTION>"):
            pass
        elif line.startswith("<SUBSECTION"):
            pass
        elif line.startswith("</SUBSECTION>"):
            pass
        elif line.startswith("<S "):
            article.sentences.append(Sentence(line,article.sections))
        else:
            pass
    return article

def instance_sentence_list(sentence_string):
    sentence_string = "<A>"+sentence_string+"</A>"
    sentence_list = []
    try:
        A = ET.fromstring(sentence_string)
        for child in A.getchildren():
            sentence_list.append(Sentence(ET.tostring(child),section_list=[]))
    except Exception as e:
        print(e)
        print(sentence_string)
        return [Sentence('<S sid="-1" ssid="-1">ERROR</S>',section_list=[])]
    return sentence_list


def get_training_entries_from_file(infile):
    labels = []
    entries = []
    for line in open(infile).readlines():
        line = line.strip()
        if line:
            try:
                line = line.replace("</S>\t\t\t<S","</S><S").replace("</S>\t\t<S","</S><S").replace("</S>\t<S","</S><S")
                leftside, rightside = line.strip().split("\t")
                e = Entry()
                blocks = rightside.split(" | ")
                labels.append(leftside)
                for field, block in zip(system_variables.header_fields, blocks):
                    value = block.replace(field + ":", "").strip()
                    e[field] = value
                entries.append(e)
            except:
                print(line)
    return entries,labels


def get_entries_from_folder(startfolder):

    entries = []
    subfolders = sorted([os.path.join(startfolder, o) for o in os.listdir(startfolder) if os.path.isdir(os.path.join(startfolder,o))])

    for folder in subfolders:
        annofolder = folder + "/annotation/"
        fin_annotation =[os.path.join(annofolder, o) for o in os.listdir(annofolder)
                         if not os.path.isdir(os.path.join(annofolder,o))][0]
        #print("******",fin_annotation)
        for line in open(fin_annotation).readlines():
            line = line.strip()
            if line:
                entry = Entry()
                blocks = line.split(" | ")
                for field,block in zip(system_variables.header_fields,blocks):
                    value = block.replace(field+":","").strip()
                    #if value.startswith("[") and value.endswith("]"):
                    #    value = ast.literal_eval(value) #cast operator for string representation of lists
                    entry[field]=value


                reference_article = str(entry['Reference Article']).replace(".txt","").replace(".xml","")+".xml"
                citing_article = str(entry['Citing Article']).replace(".txt","").replace(".xml","")+".xml"
                entry['Reference Article Content']=read_XML(folder+"/Reference_XML/"+reference_article)
                #print(citing_article)
                entry['Citing Article Content']=read_XML(folder+"/Citance_XML/"+citing_article)
                entry['Citation Text Content']=instance_sentence_list(entry['Citation Text'])
                entry['Reference Text Content']=instance_sentence_list(entry['Reference Text'])
                entries.append(entry)
    return entries

def export_to_file(outfile_predictions,out_entry_list):
    fout = open(outfile_predictions,mode="w")
    for entry in out_entry_list:
        fout.write(entry.out_file_format())
    fout.close()

