import ast
import xml.etree.ElementTree as ET
import os
import argparse


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
        for x in self['Citation Text'].split(" "):
            fv[x]=1
        return fv

    def get_ground_truth(self):
        return len(self['Reference Offset'])

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



def get_entries_from_folder(startfolder):
    header_fields = ['Citance Number', 'Reference Article','Citing Article','Citation Marker Offset','Citation Marker',
                     'Citation Offset','Citation Text','Reference Offset','Reference Text','Discourse Facet','Annotator']
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
                for field,block in zip(header_fields,blocks):
                    value = block.replace(field+":","").strip()
                    if value.startswith("[") and value.endswith("]"):
                        value = ast.literal_eval(value) #cast operator for string representation of lists
                    entry[field]=value
                reference_article = str(entry['Reference Article']).replace(".txt","").replace(".xml","")+".xml"
                citing_article = str(entry['Citing Article']).replace(".txt","").replace(".xml","")+".xml"

                entry['Reference Article Content']=read_XML(folder+"/Reference_XML/"+reference_article)
                #print(citing_article)
                entry['Citing Article Content']=read_XML(folder+"/Citance_XML/"+citing_article)
                entries.append(entry)
    return entries

def main():
    parser = argparse.ArgumentParser(description='Scisumm shared task data ')
    parser.add_argument('--train_folder',default="/Users/u6067443/proj/scisumm-corpus_revised_hector/data/Training-Set-2018")
    parser.add_argument('--test_folder')
    args = parser.parse_args()

    X_train, Y_train = [],[]
    X_test, Y_test = [],[]

    train_entries = get_entries_from_folder(args.train_folder)
    if args.test_folder:
        test_entries = get_entries_from_folder(args.test_folder)
    for e in train_entries:
        X_train.append(e.featurize())
        Y_train.append(e.get_ground_truth())

    print(X_train[:3],Y_train[:3])
if __name__ == '__main__':
    main()


