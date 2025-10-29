from typing import List
from block import Block, hash_block


def calculate_cumulative_difficulty(chain: List[Block]) -> int:
    total = 0
    for block in chain:
        leading_zeros = len(block.hash) - len(block.hash.lstrip('0'))
        total += 2 ** leading_zeros
    return total


def is_valid_chain(chain: List[Block]) -> bool:
    if len(chain) == 0:
        return False
    
    if chain[0].index != 0:
        return False
    
    for i in range(1, len(chain)):
        current_block = chain[i]
        previous_block = chain[i - 1]
        
        if current_block.index != previous_block.index + 1:
            return False
        
        if current_block.prev_hash != previous_block.hash:
            return False
        
        calculated_hash = hash_block(current_block)
        if current_block.hash != calculated_hash:
            return False
    
    return True


def compare_chains(chain_a: List[Block], chain_b: List[Block]) -> int:
    cumulative_a = calculate_cumulative_difficulty(chain_a)
    cumulative_b = calculate_cumulative_difficulty(chain_b)
    
    if cumulative_a > cumulative_b:
        return 1
    elif cumulative_b > cumulative_a:
        return -1
    else:
        if len(chain_a) > len(chain_b):
            return 1
        elif len(chain_b) > len(chain_a):
            return -1
        else:
            tip_hash_a = chain_a[-1].hash if chain_a else ""
            tip_hash_b = chain_b[-1].hash if chain_b else ""
            if tip_hash_a < tip_hash_b:
                return 1
            elif tip_hash_b < tip_hash_a:
                return -1
            else:
                return 0


def should_reorganize(current_chain: List[Block], candidate_chain: List[Block]) -> bool:
    if not is_valid_chain(candidate_chain):
        return False
    
    if len(candidate_chain) <= len(current_chain):
        comparison = compare_chains(candidate_chain, current_chain)
        if comparison <= 0:
            return False
    
    return True


def find_fork_point(chain_a: List[Block], chain_b: List[Block]) -> int:
    min_len = min(len(chain_a), len(chain_b))
    fork_index = 0
    
    for i in range(min_len):
        if chain_a[i].hash == chain_b[i].hash:
            fork_index = i
        else:
            break
    
    return fork_index
