#ifndef PadPattern_h
#define PadPattern_h

// C++ includes
#include <iostream>
#include <string>
#include <map>
#include <utility>
#include <array>
#include <sstream>
#include <stdexcept>
#include <cmath>

constexpr int nElementsPattern = 4;

unsigned int GetPatternHash(const std::array<int, nElementsPattern> &padPattern){
  unsigned int hash=0;
  for(int i=0; i<nElementsPattern; i++){
    hash += padPattern.at(i)*std::pow(128, i);
  }

  return hash;
}



class PadPattern{
public:
  PadPattern(){};
  PadPattern(const std::array<int,nElementsPattern> pads)
    :pattern(pads){
    hash = GetPatternHash(pattern);
  };
  PadPattern(const std::array<int,nElementsPattern> pads, const int _bandID, const int _phiID)
    :pattern(pads), bandID(_bandID), phiID(_phiID){
    hash = GetPatternHash(pattern);
  };
  ~PadPattern(){};

  inline int at(int gv) const {return pattern.at(gv-1);};
  inline int GetBandID() const {return bandID;};
  inline int GetPhiID() const {return phiID;};
  inline unsigned int GetHash() const {return hash;};
  void Print(bool batchMode=false) const {
    std::cout<<"[";
    for(int i=0; i<nElementsPattern; i++){
      std::cout<<pattern.at(i);
      
      if(i<(nElementsPattern-1))
	std::cout<<",";
    }
    std::cout<<"]";

    if(batchMode){
      std::cout<<","<<std::flush;
    }
    else{
      std::cout<<"band="<<bandID<<", phi="<<phiID<<std::endl;
    }
  };

  
private:
  std::array<int,nElementsPattern> pattern;
  unsigned int hash=0;
  int bandID=-1;
  int phiID=-1;
};




bool operator==(const PadPattern& lhs, const PadPattern& rhs){return lhs.GetHash()==rhs.GetHash();};
bool operator!=(const PadPattern& lhs, const PadPattern& rhs){return lhs.GetHash()!=rhs.GetHash();};
bool operator<(const PadPattern& lhs, const PadPattern& rhs){return lhs.GetHash()<rhs.GetHash();};
bool operator>(const PadPattern& lhs, const PadPattern& rhs){return lhs.GetHash()>rhs.GetHash();};




#endif
