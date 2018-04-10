import ast
import argparse

from scisumm_io_utils import system_variables
from scisumm_io_utils import Article,Section,Sentence
from scisumm_io_utils import Entry
from scisumm_io_utils import read_XML,export_to_file,instance_sentence_list,get_entries_from_folder
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description='Scisumm shared task data ')
    parser.add_argument('--train_folder',default="../scisumm-corpus_revised_hector/data/Training-Set-2018")
    parser.add_argument('--test_folder')
    parser.add_argument('--outfile_predictions_pattern',default="out/predictions_REF.txt",help="the file name must contain the string REF to be replaced")
    args = parser.parse_args()

    train_entries = get_entries_from_folder(args.train_folder)
    if args.test_folder:
        test_entries = get_entries_from_folder(args.test_folder)

    out_entries = []
    out_entries_by_ref_file = defaultdict(list)
    for e in train_entries:
        out_entry = Entry()
        for k in system_variables.header_fields_to_keep_from_gold:
            out_entry[k] = e[k]
        for k in system_variables.header_fields_for_blank_initialization:
            out_entry[k] = "BLANK"
            out_entry["Annotator"] = "Predictions"
        """The next line is the call to the baseline, which retrieves a single sentence from the Reference Document """
        predicted_ref_offset,pred_ref_text = e.sentence_scoring_baseline()
        out_entry['Reference Offset']=predicted_ref_offset
        out_entry['Reference Text']=pred_ref_text
        out_entries.append(out_entry)
        out_entries_by_ref_file[out_entry['Reference Article']].append(out_entry)

    for ref_file_name in out_entries_by_ref_file.keys():
        outfile = str(args.outfile_predictions_pattern)
        outfile=outfile.replace("REF",ref_file_name)
        export_to_file(outfile,out_entries_by_ref_file[ref_file_name])
        print("Prediction file:",outfile)

if __name__ == '__main__':
    main()


