import json
import os
import socket
import threading
import traceback
from typing import Callable, Dict, List, Optional
from block import Block, create_block_from_dict, hash_block
from consensus import should_reorganize, is_valid_chain


def list_peers(fpath: str):
    if not os.path.exists(fpath):
        print("[!] No peers file founded!")
        return []
    with open(fpath) as f:
        return [line.strip() for line in f if line.strip()]


def broadcast_block(block: Block, peers_fpath: str, port: int):
    print("[BROADCAST] Broadcasting block...")
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer, port))
            s.send(json.dumps({"type": "block", "data": block.as_dict()}).encode())
            s.close()
        except Exception as e:
            print(f"[BROADCAST_BLOCK] Failed to send to {peer}: {e}")


def broadcast_transaction(tx: Dict, peers_fpath: str, port: int):
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer, port))
            s.send(json.dumps({"type": "tx", "data": tx}).encode())
            s.close()
        except Exception as e:
            print(
                f"[BROADCAST_TX] Exception during comunication with {peer}. Exception: {e}"
            )


def request_chain_from_peer(peer_host: str, port: int) -> Optional[List[Block]]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((peer_host, port))
        s.send(json.dumps({"type": "get_chain"}).encode())
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        
        s.close()
        
        response = json.loads(data.decode())
        if response["type"] == "chain":
            chain_data = response["data"]
            chain = [create_block_from_dict(b) for b in chain_data]
            return chain
    except Exception as e:
        print(f"[SYNC] Failed to get chain from {peer_host}: {e}")
    return None


def sync_with_peers(blockchain: List[Block], peers_fpath: str, port: int, blockchain_fpath: str, on_valid_block_callback: Callable) -> bool:
    peers = list_peers(peers_fpath)
    reorganized = False
    
    for peer in peers:
        peer_chain = request_chain_from_peer(peer, port)
        if peer_chain and should_reorganize(blockchain, peer_chain):
            print(f"[REORG] Reorganizing chain from peer {peer}")
            print(f"[REORG] Old chain length: {len(blockchain)}, New chain length: {len(peer_chain)}")
            blockchain.clear()
            blockchain.extend(peer_chain)
            on_valid_block_callback(blockchain_fpath, blockchain)
            reorganized = True
            break
    
    return reorganized


def handle_client(
    conn: socket.socket,
    addr: str,
    blockchain: List[Block],
    difficulty: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
    peers_fpath: str,
    port: int,
):
    try:
        data = conn.recv(8192).decode()
        msg = json.loads(data)
        
        if msg["type"] == "block":
            block = create_block_from_dict(msg["data"])
            expected_hash = hash_block(block)
            
            if not (block.hash.startswith("0" * difficulty) and block.hash == expected_hash):
                print(f"Invalid block received from {addr}: invalid PoW or hash")
                conn.close()
                return
            
            if block.prev_hash == blockchain[-1].hash and block.index == len(blockchain):
                blockchain.append(block)
                on_valid_block_callback(blockchain_fpath, blockchain)
                print(f"[OK] New valid block {block.index} added from {addr}")
            else:
                print(f"[FORK] Potential fork detected from {addr}. Block index: {block.index}, Expected: {len(blockchain)}")
                print(f"[SYNC] Synchronizing with peers to resolve fork...")
                sync_with_peers(blockchain, peers_fpath, port, blockchain_fpath, on_valid_block_callback)
        
        elif msg["type"] == "tx":
            tx = msg["data"]
            if tx not in transactions:
                transactions.append(tx)
                print(f"[+] Transaction received from {addr}")
        
        elif msg["type"] == "get_chain":
            chain_data = [b.as_dict() for b in blockchain]
            response = json.dumps({"type": "chain", "data": chain_data})
            conn.send(response.encode())
            print(f"[SYNC] Sent chain to {addr}")
    
    except Exception as e:
        print(f"[ERROR] Exception when handling client: {e}")
        print(traceback.format_exc())
    
    conn.close()


def start_server(
    host: str,
    port: int,
    blockchain: List[Block],
    difficulty: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
    peers_fpath: Optional[str] = None,
):
    def server_thread():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"[SERVER] Listening on {host}:{port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(
                    conn,
                    addr,
                    blockchain,
                    difficulty,
                    transactions,
                    blockchain_fpath,
                    on_valid_block_callback,
                    peers_fpath,
                    port,
                ),
            ).start()

    threading.Thread(target=server_thread, daemon=True).start()
