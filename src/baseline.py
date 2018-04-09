import ast
import argparse

from scisumm_io_utils import system_variables
from scisumm_io_utils import Article,Section,Sentence
from scisumm_io_utils import Entry
from scisumm_io_utils import read_XML,export_to_file,instance_sentence_list,get_entries_from_folder


def main():
    parser = argparse.ArgumentParser(description='Scisumm shared task data ')
    parser.add_argument('--train_folder',default="../scisumm-corpus_revised_hector/data/Training-Set-2018")
    parser.add_argument('--test_folder')
    parser.add_argument('--outfile_predictions',default="predictions.txt")
    args = parser.parse_args()

    train_entries = get_entries_from_folder(args.train_folder)
    if args.test_folder:
        test_entries = get_entries_from_folder(args.test_folder)

    out_entries = []
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

    export_to_file(args.outfile_predictions,out_entries)
    print("Prediction file:",args.outfile_predictions)

if __name__ == '__main__':
    main()


