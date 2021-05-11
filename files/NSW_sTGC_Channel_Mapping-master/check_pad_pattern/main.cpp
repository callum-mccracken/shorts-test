/////////////////////////////////////////////////////////////
// Checks wheter a series of quadruplet pads are part      //
// of a pad pattern based on the list provided by Yoram Rozen.
// Can also generate a list of patterns based on the geometry XML files
// of the sTGC cosmic-ray analysis.
//
// Author: Benoit Lefebvre            Creation: 2019-11-20
//         benoit.lefebvre@cern.ch
/////////////////////////////////////////////////////////////


// C++ includes
#include <iostream>
#include <string>
#include <map>
#include <utility>
#include <array>
#include <vector>
#include <sstream>
#include <fstream>
#include <stdexcept>
#include <cmath>
#include <set>

// ROOT includes
// ...


// My includes
#include "PadPattern.h"

using namespace std;


int InteruptForArgumentError(const int returnCode=0, const string &returnMessage=""){
  string usage = "./CheckPadPattern quad_type [-GV1 id1] [-GV2 id2] [-GV3 id3] [-GV4 id4] [--batch-mode]";
  if(!returnMessage.empty()){
    cout<<returnMessage<<endl;
  }

  cout<<usage<<endl;
  return returnCode;
};
int ThrowInvalidArguments(){return InteruptForArgumentError(2, "Invalid arguments.");};
map<int,map<int,int>> GetTriggerPadMap(const string &quadTypeStr);
set<PadPattern> GetPadPatterns(const string &quadTypeStr);
bool ValidateModuleTypeStr(const string &moduleTypeStr);
string GetModuleTypeStr(const int moduleTypeIdx);

int main(int argc, char **argv){

  // Parse arguments
  //  cout<<"**** CheckPadPattern ****"<<endl;

  if(argc==1)
    return InteruptForArgumentError();  
  else if(argc<4)
    return InteruptForArgumentError(1, "A list of pads must be specified.");

  string quadTypeStr(argv[1]);
  if(!ValidateModuleTypeStr(quadTypeStr))
    return InteruptForArgumentError(5, "Invalid quadruplet type");
  
  map<int,int> testPads; // Pads to be check for different gas volumes
  int iArg = 2;
  bool batchMode=false;
  while(iArg<argc){
    if(string(argv[iArg])=="--batch-mode"){
      batchMode=true;
      iArg++;
      continue;
    }

    string lFlag(argv[iArg]);
    int gv=-1;
    if(lFlag.size()==4 && lFlag.substr(0,3)=="-GV"){
      gv=lFlag[3]-'0';
    }
    else return ThrowInvalidArguments();

    if(gv<1 || gv>4) return ThrowInvalidArguments();

    iArg++;
    
    if(iArg>=argc) return ThrowInvalidArguments();

    int id = atoi(argv[iArg]);
    if(id<=0) return ThrowInvalidArguments();
    
    bool ret = testPads.insert(pair<int,int>(gv,id)).second;
    if(!ret)
      return InteruptForArgumentError(3, "Duplicate gas volume detected!");

    iArg++;
  }
    
  
  const int nPads = testPads.size();

  if(!batchMode){
    cout<<"Testing set of "<<testPads.size()<<" pads."<<endl;
    cout<<"Testing for quadruplet: "<<quadTypeStr<<endl;
    for(const auto &p : testPads){
      cout<<"   GV"<<p.first<<" ID"<<p.second<<endl;
    }
  }

  set<PadPattern> padPatterns = GetPadPatterns(quadTypeStr);

  
  int countMatch=0;
  for(const auto &pattern : padPatterns){
    bool haveMatch=true;
    for(const auto &p : testPads){
      int gv = p.first;
      int id = p.second;
      if(pattern.at(gv)!=id){
	haveMatch=false;
      }
    }

    //    pattern.Print();
    if(haveMatch){
      if(!batchMode){
	cout<<"Found matching pattern:"<<endl;
      }
      pattern.Print(batchMode);
      countMatch++;
    }
  }

  if(countMatch==0){
    if(batchMode){
      cout<<"-"<<std::flush;
    }
    else{
      cout<<"Found no matching pad pattern."<<endl;
    }
  }

  if(batchMode){
    cout<<endl;
  }
  
  // For debugging purposes
  //  for(const auto &pattern : padPatterns){
  //    pattern.Print();
  //  }
 

  return 0;
}


bool ValidateModuleTypeStr(const string &moduleTypeStr){
  if(moduleTypeStr.size()!=4) return false;
  if(moduleTypeStr[0]!='Q') return false;
  if(!(moduleTypeStr[1]=='S' || moduleTypeStr[1]=='L')) return false;
  int id = moduleTypeStr[2]-'0';
  if(id<1 || id>3) return false;
  if(!(moduleTypeStr[3]=='P' || moduleTypeStr[3]=='C')) return false;
  return true;
}

string GetModuleTypeStr(const int moduleTypeIdx){
  switch(moduleTypeIdx){
  case 1: return "QS1";
  case 2: return "QS2";
  case 3: return "QS3";
  case 4: return "QL1";
  case 5: return "QL2";
  case 6: return "QL3";
  default: return "";
  }
}
 

// Returns a map which stores the QUADELECTRODEID which can be accessed
// using the gas volume and trigger pad as key.
map<int,map<int,int>> GetTriggerPadMap(const string &quadTypeStr){
  map<int,map<int,int>> mapping;
  ifstream inFile("../mapping.txt");
  if(!inFile.is_open()){
    throw runtime_error("Cannot open the mapping file.");
  }

  string line;
  while(getline(inFile, line)){
    istringstream iss(line);
    string item;
    
    iss>>item;
    if(item!=quadTypeStr){
      continue;
    }

    iss>>item;
    int gv = atoi(item.c_str());

    iss>>item;
    iss>>item;
    if(item!="pad")
      continue;

    iss>>item;
    iss>>item;
    iss>>item;
    int quadID = atoi(item.c_str()); 

    iss>>item;
    iss>>item;
    iss>>item;
    iss>>item;
    iss>>item;
    iss>>item;
    int triggerPad = atoi(item.c_str()); 

    mapping[gv][triggerPad] = quadID;
  }

  if(mapping.empty() || mapping.size()!=4){
    throw runtime_error("Could not parse a valid mapping.");
  }
  
  inFile.close();
  return mapping;
}


// Parses the pattern file and get the patterns for the specified quadruplet type
// in terms of the QUADELECTRODEID mapping.
// Both patterns.txt and TRpattern.txt files are parsed
set<PadPattern> GetPadPatterns(const string &quadTypeStr){
  map<int,map<int,int>> triggerPadMap = GetTriggerPadMap(quadTypeStr);
  
  set<PadPattern> padPatterns;

  //*******************************
  // Parse patterns.txt
  {
    ifstream inFile("patterns.txt");
    if(!inFile.is_open()){
      throw runtime_error("Cannot open file 'patterns.txt'.");
    }
    
    string line;
    while(getline(inFile, line)){
      if(line[0]=='#')
	continue;
      
      istringstream iss(line);
      string item;
      set<string> quadTypeSet;
      vector<int> fullPattern(8);
      for(int col=0; col<8; col++){
	iss>>item;
	int globalPadID = atoi(item.c_str());
	int moduleIdx = globalPadID/1000;
	int triggerPadID = globalPadID % 1000;
	string quadTypeStr = GetModuleTypeStr(moduleIdx);

	//      cout<<"col="<<col<<", item="<<item<<endl;
	//      cout<<"ROGER: moduleIdx="<<moduleIdx<<endl;
	
	if(quadTypeStr.empty()){
	  throw runtime_error("Cannot recognize this module type.");
      }
	
	quadTypeSet.insert(quadTypeStr);
	fullPattern.at(col) = triggerPadID;
      }
      
      iss>>item;
      int bandID = atoi(item.c_str());
      iss>>item;
      int phiID = atoi(item.c_str());
      
      
      if(quadTypeSet.size()!=1){
	cout<<"WARNING: Not all module types are the same for pattern!"<<endl;
	continue;
      }
      
      string currentQuadType = *(quadTypeSet.begin());
      if(quadTypeStr.substr(0,3)!=currentQuadType){
	continue;
      }
      
      char triggerLogic = quadTypeStr[3];
      char wedgeSize = quadTypeStr[1];
      array<int,nElementsPattern> padArray, padArrayRemapped;
      if(wedgeSize=='S' && triggerLogic=='P'){
	for(int i=4; i<8; i++){
	  padArray.at(i-4) = fullPattern.at(i);
	}
      }
      else if(wedgeSize=='S' && triggerLogic=='C'){
	for(int i=3; i>=0; i--){
	  padArray.at(3-i) = fullPattern.at(i); 
	}
      }
      else if(wedgeSize=='L' && triggerLogic=='P'){
	for(int i=0; i<4; i++){
	  padArray.at(i) = fullPattern.at(i); 
	}
      }
      else if(wedgeSize=='L' && triggerLogic=='C'){
	for(int i=7; i>=4; i--){
	  padArray.at(7-i) = fullPattern.at(i); 
	}
      }
      else throw runtime_error("Invalid module type.");

      for(int i=0; i<4; i++){
	padArrayRemapped.at(i) = triggerPadMap.at(i+1).at(padArray.at(i));
      }
      
      bool ret = padPatterns.insert( PadPattern(padArrayRemapped, bandID, phiID) ).second;
      // Removed this check because duplicates are actually expected
      /*
	if(!ret){
	cout<<"WARNING: Inserted pad pattern which already exists!"<<endl;
	cout<<"Pattern: ";
	PadPattern(padArrayRemapped, bandID, phiID).Print();
	}
      */
    } // End reading file
    
    inFile.close();
  }
  // Finished parsing patterns.txt
  //*******************************


  //**************************
  // Parse TRpattern.txt file
  if(true){
    ifstream inFile("TRpattern.txt");
    if(!inFile.is_open()){
      throw runtime_error("Cannot open file 'TRpattern.txt'.");
    }
    
    string line;
    while(getline(inFile, line)){
      if(line[0]=='#')
	continue;
      
      istringstream iss(line);
      string item;
      set<string> quadTypeSet;
      vector<int> fullPattern(4);

      iss>>item;
      string towerType; // Can be either 'inner' or 'outer'
      if(item=="RiccardoTRinner"){
	towerType="inner";
      }
      else if(item=="RiccardoTRouter"){
	towerType="outer";
      }
      else throw runtime_error("Cannot recognize tower type in TRpattern.txt");

      for(int col=0; col<4; col++){
	iss>>item;
	int globalPadID = atoi(item.c_str());
	int moduleIdx = globalPadID/1000;
	int triggerPadID = globalPadID % 1000;
	string quadTypeStr = GetModuleTypeStr(moduleIdx);
	
	//      cout<<"col="<<col<<", item="<<item<<endl;
	//      cout<<"ROGER: moduleIdx="<<moduleIdx<<endl;
	
	if(quadTypeStr.empty()){
	  throw runtime_error("Cannot recognize this module type.");
	}
	
	quadTypeSet.insert(quadTypeStr);
	fullPattern.at(col) = triggerPadID;
      }
      
      iss>>item;
      int bandID = atoi(item.c_str());
      iss>>item;
      int phiID = atoi(item.c_str());
      
      

      
      if(quadTypeSet.size()!=1){
	cout<<"WARNING: Not all module types are the same for pattern!"<<endl;
	continue;
      }

      string currentQuadType = *(quadTypeSet.begin());
      if(quadTypeStr.substr(0,3)!=currentQuadType){
	continue;
      }


      //cout<<"New pattern: "<<towerType<<" "<<fullPattern.at(0)<<" "<<fullPattern.at(1)<<" "<<fullPattern.at(2)<<" "<<fullPattern.at(3)<<" "<<bandID<<" "<<phiID<<endl;
      
      char wedgeSize = quadTypeStr[1];
      char triggerLogic;

      if(towerType=="outer" && wedgeSize=='L'){
	triggerLogic='C';
      }
      else if(towerType=="outer" && wedgeSize=='S'){
	triggerLogic='P';
      }
      else if(towerType=="inner" && wedgeSize=='L'){
	triggerLogic='P';
      }
      else if(towerType=="inner" && wedgeSize=='S'){
	triggerLogic='C';
      }
      else throw logic_error("Invalid wedge_size+trigger_tower combination.");

      if(triggerLogic != quadTypeStr[3]){
	continue;
      }

      //      cout<<"New pattern: "<<towerType<<" "<<triggerLogic<<" "<<fullPattern.at(0)<<" "<<fullPattern.at(1)<<" "<<fullPattern.at(2)<<" "<<fullPattern.at(3)<<" "<<bandID<<" "<<phiID<<endl;

      
      array<int,nElementsPattern> padArray, padArrayRemapped;
      for(int i=0; i<4; i++){
	if(triggerLogic=='P'){
	  padArray.at(i) = fullPattern.at(i);
	}
	else if(triggerLogic=='C'){
	  padArray.at(3-i) = fullPattern.at(i);
	}
	else throw logic_error("Invalid trigger logic.");
      }

      for(int i=0; i<4; i++){
	padArrayRemapped.at(i) = triggerPadMap.at(i+1).at(padArray.at(i));
      }

      auto ret = padPatterns.insert( PadPattern(padArrayRemapped, bandID, phiID) );
      /*
      if(ret.second){
	cout<<"Inserted new pattern:";
	ret.first->Print();
      }
      */
      
    } // End reading file
    
    inFile.close();
  }
  // Finished parsing TRpattern.txt file
  //**************************

  return padPatterns;
}






