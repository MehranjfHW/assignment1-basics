import heapq               # findind the most frequent pairs
from pathlib import Path   # directory and file path manipulation
import urllib.request    # for downloading files from the web

import regex as re       # processing text with regular expressions




def download_token_data(token_data_path:Path, token_data_file_name : str, url:str)->None:
    #Downloading the tokenizer data given a directory path as Path objet and file name
    
    
     token_data_file_path=token_data_path /token_data_file_name                                             # creating a Path object for the text file
        

     token_data_path.mkdir(exist_ok=True)  # create the data directory if it doesn't exist
    
     if token_data_file_path.is_file():  # check if the file already exists or the download is failed
            print("A file exists in the given path")
            return None
     attempt=0
     while attempt<5:
        try:
            attempt +=1
            print("Downloading the text file from the web...")
            urllib.request.urlretrieve(url, token_data_file_path) #download the text file and save it in the data directory
            print("Download was successful")
            break
        except:
            if attempt==5:
                print("I am tired of doanloading, it is not working.")
            print("Failed to download the text file. Let's try again.")
            
     return None







def reverse_bytes(token: bytes) -> tuple:
    """Reverse the bytes of a token.
       heapq is a min-heap, so we need to reverse the bytes to get the correct order."""
    return tuple(-b for b in token) + (1,)

def heap_entry(pair: tuple, freq: int) -> tuple:
    """Create a heap entry for a pair of tokens and its frequency.
       The entry is a tuple of (negative frequency, reversed bytes of the first token, reversed bytes of the second token, the pair itself).
       This allows us to use heapq to find the most frequent pairs."""
       
    return (
        -freq,
        reverse_bytes(pair[0]),
        reverse_bytes(pair[1]),
        pair
    )






def count_expressions_in_string(story: str, PAT: str, counts: dict) -> None:
    " reading a story and counting the frequency of each regular expression match in the story"
    
    
    regex_file=re.finditer(PAT, story)
    
    for match in regex_file:
        
        if match.group() not in counts:
            
            counts[match.group()] = 1
            
        else:
            
            counts[match.group()] += 1
                

def count_tokens_in_file(file_path: Path, PAT: str, special_tokens: list, chunk_size: int = 65536) -> dict:
    """Count the frequency of each regular expression match in a text file."""
    pattern = "|".join(
    re.escape(token)
    for token in sorted(special_tokens, key=len, reverse=True))
    buffer = ""            # store the unfinished story from each iteration
    counts = {}            # initialize an empty dictionary to store the counts of regular expression matches in utf-8 encoded
    story_count = 0        # initialize the story count to 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        
           while chunk := f.read(chunk_size):  # read the file in chunks of size chunk_size
               
              buffer += chunk    #add the chunk to the unfinished story from the previous iteration     
                       
              parts = re.split(pattern, buffer)    #devide the buffer into stories using the dividing string
              
              buffer = parts.pop()                  # store the last part of the buffer as the unfinished story for the next iteration
              
              for story in parts:
                  
                  if story_count % 100000 == 0:
                      
                    print(f"Story {story_count+1} is reading")
                       
                  count_expressions_in_string(story, PAT, counts)  #update the counts dictionary with the counts of regular expression matches in the story
                  
                  story_count += 1
                  
           if buffer:
               
               count_expressions_in_string(buffer, PAT, counts)  #update the counts dictionary with the last unfinished story in the buffer
               story_count += 1
               
    byte_counts = {
    tuple(bytes([b]) for b in word.encode("utf-8")): freq
    for word, freq in counts.items()
}                  #updating the counts dictionry to use bytes instead of strings
               
    return byte_counts


def initialize_vocab(special_tokens:list=[]) -> dict:
    """Initialize the vocabulary with single-byte tokens."""
    vocab={i: bytes([i]) for i in range(256)}
    for i, token in enumerate(special_tokens):
       vocab[256+i] = bytes(token, "utf-8")
    return vocab


def update_pairs_freq_p(comb: tuple, freq: int, pairs_freq: dict) -> None:
    
    for index in range(len(comb) - 1):
               
        pair=(comb[index], comb[index + 1])
        if pair not in pairs_freq:
            pairs_freq[pair] = freq
        else:
            pairs_freq[pair] += freq
    return None
                    
def  update_pair_to_combs_p(comb: tuple, pair_to_combs: dict):
    
        for index in range(len(comb) - 1):
           pair = (comb[index], comb[index + 1])
           if pair not in pair_to_combs:
               s_comb = {comb}
               pair_to_combs[pair] = s_comb
           else:
                pair_to_combs[pair].add(comb)


def update_comb_new_token(comb: tuple, best_pair: tuple) -> tuple:
        
        new_token=best_pair[0]+ best_pair[1]
        new_comb = []
        index = 0
        while index < len(comb):
            if index < len(comb) - 1 and (comb[index], comb[index + 1]) == best_pair:
                new_comb.append(new_token)
              
                index += 2
                
              
            else:
               new_comb.append(comb[index])
               index += 1
        new_comb = tuple(new_comb)
        
        return new_comb
    
def update_pairs_freq_changed_pairs(comb: tuple, new_comb:tuple, freq:int, pairs_freq:dict, changed_pairs:dict) -> None:

          
    for i in range(len(comb) - 1):
        pair = (comb[i], comb[i + 1])
        pairs_freq[pair] -= freq
        if pairs_freq[pair] == 0:
            del pairs_freq[pair]
            
        changed_pairs.add(pair)
            
            
            
    for i in range(len(new_comb) - 1):
        pair = (new_comb[i], new_comb[i + 1])
        pairs_freq[pair] = pairs_freq.get(pair, 0) + freq
               
        changed_pairs.add(pair)
               
    return None
        
def update_byte_counts(comb: tuple, new_comb:tuple, freq:int, byte_counts:dict) -> None:
               
        byte_counts[new_comb] = byte_counts.get(new_comb, 0) + freq
        try:
            del byte_counts[comb]
        except KeyError:
            pass
        
        return None
    
def  update_pair_to_combs(comb: tuple, new_comb:tuple, pair_to_combs: dict) ->None:
        
        
        for index in range(len(comb) - 1):
           pair = (comb[index], comb[index + 1])
           try:
               pair_to_combs[pair].discard(comb)
           except KeyError:
               pass
             
        for index in range(len(new_comb) - 1):
            pair = (new_comb[index], new_comb[index + 1])
            if pair not in pair_to_combs:
                s_new_comb = {new_comb}
                pair_to_combs[pair] = s_new_comb
            else:
                pair_to_combs[pair].add(new_comb)
                
        return None
    
def update_pairs_freq_heap(changed_pairs:set,pairs_freq_heap:heapq,  pairs_freq:dict) -> None:
                
        for pair in changed_pairs:
           if pair in pairs_freq:
             heapq.heappush(pairs_freq_heap,heap_entry(pair, pairs_freq[pair]))
        return None
    
def  pick_best_pair(pairs_freq_heap:heapq,pairs_freq:dict)-> tuple:
    best_pair = None
    while pairs_freq_heap:
        freq_min,_,_, pair = heapq.heappop(pairs_freq_heap)
        
        if pairs_freq.get(pair, 0) == -freq_min:
            best_pair = pair
            break
    return best_pair



def enlarging_vocab(vocab:dict, intended_vocab_size:int, byte_counts:dict, pairs_freq:dict=None, pairs_freq_heap:dict=None, pair_to_combs:dict=None, changed_pairs:dict=None, merges:list=None) -> tuple:
  
   merges=[]

   while  len(vocab) < intended_vocab_size:
       
       changed_pairs = set()  #storing pairs whoses frequencies need to change after vocab is updated
       
       if pairs_freq==None:    # initialise
        
           pairs_freq = {}   #storing frequency of each pair in data set

           pairs_freq_heap = []   #storing frequency of each pair in data set in heapq for finding the most frequent

           pair_to_combs={}       #storing which regular expressions contains the pair

           

        
        
           for comb , freq in byte_counts.items():
    
              update_pairs_freq_p(comb, freq, pairs_freq)
        
           for comb in byte_counts.keys():
    
               update_pair_to_combs_p(comb, pair_to_combs)
  
            
            
           for pair, freq in pairs_freq.items():
    
                pairs_freq_heap.append(heap_entry(pair, freq))
    
           heapq.heapify(pairs_freq_heap)          # sorting
    
    
           


       
       
       best_pair=pick_best_pair(pairs_freq_heap,pairs_freq)
                
       if best_pair is None:
            break
    
       merges.append(best_pair)
            
       new_token = best_pair[0] + best_pair[1]
            
       vocab[len(vocab)] = new_token
        
       if len(vocab) % 100 == 0:
          print(f"vocab size: {len(vocab)}")
      
       
       
       
       for comb in pair_to_combs.get(best_pair, set()).copy():
        
        
            new_comb=update_comb_new_token(comb, best_pair)
       
            if new_comb!= comb:
        
                 freq = byte_counts.get(comb, 0)
    
                 update_pairs_freq_changed_pairs(comb, new_comb,freq, pairs_freq, changed_pairs)
        
         
         
                 update_byte_counts(comb, new_comb, freq, byte_counts)
               
                 update_pair_to_combs(comb, new_comb, pair_to_combs)
           
        
       update_pairs_freq_heap(changed_pairs,pairs_freq_heap, pairs_freq)
                
        
         
              
   return vocab, byte_counts, pairs_freq, pairs_freq_heap, pair_to_combs, merges





# ------------------------------------------------------  Encoder functions


def  match_encoded(match:str ,bytes_to_id : dict ,encoded_matches :dict, merges:list) -> list[int] :
    
    match_bytes=[bytes([b]) for b in match.encode("utf-8")]
    
    for byte_1, byte_2 in merges:
        match_bytes_new=[]
        index=0
        while index <len(match_bytes):
            if index <len(match_bytes)-1 and byte_1==match_bytes[index] and byte_2==match_bytes[index+1]:
                match_bytes_new.append(byte_1+byte_2)
                index +=2
                
            else:
                match_bytes_new.append(match_bytes[index])
                index +=1
            
        match_bytes=match_bytes_new
        
    match_encoded=[bytes_to_id[x] for x in match_bytes]
    
    encoded_matches[match]=match_encoded
    
    return match_encoded
        
        
        
        
        
        
        
            
            
    
    




def story_encoded(story:str, PAT:str, bytes_to_id:dict, encoded_matches:dict, merges:list) -> list[int]:
    """ encoding a story"""
    
    regex_file=re.finditer(PAT, story)      #finding regular expression in the story
    
    story_encoded=[]      #initialising the list storing the encoding
    
    for match in regex_file:
        
        if match.group() in encoded_matches:
            
            story_encoded += encoded_matches[match.group()]
        
        else:
            
            story_encoded += match_encoded(match.group() , bytes_to_id, encoded_matches, merges)
            
        
    return story_encoded



def text_encoder(text:str, PAT:str, bytes_to_id:dict, special_tokens:list[str], merges:list ) -> list[int]:
    
    
    encoded_matches={}         # A dictionary to save the encoding of a regular expression after applying PAT
     
    re_pecial_tokens = "|".join(
    re.escape(token)
    for token in sorted(special_tokens, key=len, reverse=True))
    
    text_encoded =[]            # initialize an empty list to store the encoding
    
    if special_tokens:
       parts_special_tokens = re.split(f"({re_pecial_tokens})", text) #devide the buffer into stories or special tokens using the special tokens
    else:
       parts_special_tokens = [text]                                  #case with no special token
              
                       
              
              
              
    for story in parts_special_tokens:
                  
        if story in special_tokens:                       
                      
            text_encoded.append(bytes_to_id[story.encode("utf-8")])
                      
        else:
                      
            text_encoded +=story_encoded(story, PAT, bytes_to_id,encoded_matches, merges)
                  
                  
                  
    
               
    return text_encoded 