// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title AuditAnchor
/// @notice Stores Merkle roots of batches of audit_trail.row_hash values.
/// One state-changing function only, by design (Master Context, Section 8):
/// no clinical, patient, or regulatory data is ever written on-chain.
contract AuditAnchor {
    /// @dev block.timestamp => committed Merkle root
    mapping(uint256 => bytes32) public commits;

    event RootCommitted(uint256 indexed timestamp, bytes32 merkleRoot);

    function commitRoot(bytes32 merkleRoot) public {
        commits[block.timestamp] = merkleRoot;
        emit RootCommitted(block.timestamp, merkleRoot);
    }
}
