// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract Insurance {
    string[] _claimsby;
    string[] _claimsfor;
    uint[] _claimsids;
    uint[] _claimages;
    string[] _phonenos;
    string[] _dobs;
    string[] _address;
    string[] _diagnosis;
    string[] _claimMonth;
    string[] _amounts;
    string[] _filehashes;
    uint[] _statuses;

    function addClaim(
        string memory claimby,
        string memory claimfor,
        uint claimid,
        uint claimage,
        string memory phone,
        string memory dob,
        string memory caddress,
        string memory diagnosis,
        string memory claimmonth,
        string memory amount,
        string memory filehash) public {
            _claimsby.push(claimby);
            _claimsfor.push(claimfor);
            _claimsids.push(claimid);
            _claimages.push(claimage);
            _phonenos.push(phone);
            _dobs.push(dob);
            _address.push(caddress);
            _diagnosis.push(diagnosis);
            _claimMonth.push(claimmonth);
            _amounts.push(amount);
            _filehashes.push(filehash);
            _statuses.push(0);
        }
    
    function viewClaims() public view returns(string[] memory,string[] memory,uint[] memory,uint[] memory,string[] memory,string[] memory,string[] memory,string[] memory, string[] memory,string[] memory,uint[] memory,string[] memory) {
        return(_claimsby,_claimsfor,_claimsids,_claimages,_phonenos,_dobs,_address,_diagnosis,_claimMonth,_amounts,_statuses,_filehashes);
    }

    function updateClaim(uint id1,uint status1) public {
        uint i;

        for (i=0;i<_claimsids.length;i++){
            if(_claimsids[i]==id1){
                _statuses[i]=status1;
            }
        }
    }
}
