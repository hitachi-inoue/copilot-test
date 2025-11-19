#!/usr/bin/env python3
"""
Product Backlog Item (PBI) Validation Script

このスクリプトは、backlog/ディレクトリ内のすべてのPBIファイルを検証し、
構造の整合性をチェックします。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set


def validate_pbi_structure(pbi_data: Dict, filename: str) -> List[str]:
    """PBIデータの構造を検証する"""
    errors = []
    
    # 必須フィールドの確認
    required_fields = ['id', 'title', 'description', 'status', 'priority', 'estimatedPoints', 'acceptanceCriteria', 'tasks']
    for field in required_fields:
        if field not in pbi_data:
            errors.append(f"{filename}: 必須フィールド '{field}' が見つかりません")
    
    # ステータスの検証
    valid_statuses = ['Ready', 'In Progress', 'Done']
    if 'status' in pbi_data and pbi_data['status'] not in valid_statuses:
        errors.append(f"{filename}: 無効なステータス '{pbi_data['status']}' (有効値: {', '.join(valid_statuses)})")
    
    # 優先度の検証
    valid_priorities = ['High', 'Medium', 'Low']
    if 'priority' in pbi_data and pbi_data['priority'] not in valid_priorities:
        errors.append(f"{filename}: 無効な優先度 '{pbi_data['priority']}' (有効値: {', '.join(valid_priorities)})")
    
    # タスクの検証
    if 'tasks' in pbi_data:
        task_ids = set()
        for i, task in enumerate(pbi_data['tasks']):
            task_errors = validate_task_structure(task, i, filename, task_ids)
            errors.extend(task_errors)
            
            # タスクIDの重複チェック
            if 'id' in task:
                if task['id'] in task_ids:
                    errors.append(f"{filename}: 重複したタスクID '{task['id']}'")
                task_ids.add(task['id'])
        
        # 依存関係の検証
        for task in pbi_data['tasks']:
            if 'dependencies' in task and task['dependencies']:
                for dep_id in task['dependencies']:
                    if dep_id not in task_ids:
                        errors.append(f"{filename}: タスク {task['id']} の依存関係 '{dep_id}' が見つかりません")
    
    return errors


def validate_task_structure(task: Dict, index: int, filename: str, all_task_ids: Set[str]) -> List[str]:
    """タスクデータの構造を検証する"""
    errors = []
    
    # 必須フィールドの確認
    required_task_fields = ['id', 'title', 'description', 'estimatedHours', 'status']
    for field in required_task_fields:
        if field not in task:
            errors.append(f"{filename}: タスク[{index}] に必須フィールド '{field}' が見つかりません")
    
    # タスクステータスの検証
    valid_task_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
    if 'status' in task and task['status'] not in valid_task_statuses:
        errors.append(f"{filename}: タスク {task.get('id', index)} に無効なステータス '{task['status']}' (有効値: {', '.join(valid_task_statuses)})")
    
    # 見積時間の検証
    if 'estimatedHours' in task:
        if not isinstance(task['estimatedHours'], (int, float)) or task['estimatedHours'] <= 0:
            errors.append(f"{filename}: タスク {task.get('id', index)} の見積時間が無効です")
    
    return errors


def generate_statistics(pbi_files: List[Path]) -> Dict:
    """統計情報を生成する"""
    stats = {
        'total_pbis': 0,
        'total_tasks': 0,
        'total_hours': 0,
        'tasks_by_status': {'TODO': 0, 'IN_PROGRESS': 0, 'DONE': 0},
        'pbis_by_priority': {'High': 0, 'Medium': 0, 'Low': 0},
        'pbis_by_status': {'Ready': 0, 'In Progress': 0, 'Done': 0}
    }
    
    for filepath in pbi_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                pbi_data = json.load(f)
                
            stats['total_pbis'] += 1
            
            if 'priority' in pbi_data:
                stats['pbis_by_priority'][pbi_data['priority']] = stats['pbis_by_priority'].get(pbi_data['priority'], 0) + 1
            
            if 'status' in pbi_data:
                stats['pbis_by_status'][pbi_data['status']] = stats['pbis_by_status'].get(pbi_data['status'], 0) + 1
            
            if 'tasks' in pbi_data:
                for task in pbi_data['tasks']:
                    stats['total_tasks'] += 1
                    if 'estimatedHours' in task:
                        stats['total_hours'] += task['estimatedHours']
                    if 'status' in task:
                        stats['tasks_by_status'][task['status']] = stats['tasks_by_status'].get(task['status'], 0) + 1
        except Exception as e:
            print(f"警告: {filepath} の統計処理中にエラー: {e}")
    
    return stats


def main():
    """メイン処理"""
    backlog_dir = Path(__file__).parent / 'backlog'
    
    if not backlog_dir.exists():
        print("エラー: backlog/ ディレクトリが見つかりません")
        sys.exit(1)
    
    pbi_files = sorted(backlog_dir.glob('pbi-*.json'))
    
    if not pbi_files:
        print("エラー: PBIファイルが見つかりません")
        sys.exit(1)
    
    print(f"検証中: {len(pbi_files)} 個のPBIファイル\n")
    
    all_errors = []
    
    for filepath in pbi_files:
        print(f"✓ 検証中: {filepath.name}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                pbi_data = json.load(f)
            
            errors = validate_pbi_structure(pbi_data, filepath.name)
            all_errors.extend(errors)
            
            if not errors:
                print(f"  ✓ {pbi_data.get('id', 'Unknown')}: {pbi_data.get('title', 'Unknown')} - {len(pbi_data.get('tasks', []))} タスク")
        except json.JSONDecodeError as e:
            error_msg = f"{filepath.name}: JSON解析エラー: {e}"
            all_errors.append(error_msg)
            print(f"  ✗ {error_msg}")
        except Exception as e:
            error_msg = f"{filepath.name}: エラー: {e}"
            all_errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    print()
    
    # 統計情報の表示
    stats = generate_statistics(pbi_files)
    print("=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総PBI数: {stats['total_pbis']}")
    print(f"総タスク数: {stats['total_tasks']}")
    print(f"総見積時間: {stats['total_hours']} 時間")
    print()
    print("タスクステータス:")
    for status, count in stats['tasks_by_status'].items():
        percentage = (count / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
        print(f"  {status}: {count} ({percentage:.1f}%)")
    print()
    print("PBI優先度:")
    for priority, count in stats['pbis_by_priority'].items():
        if count > 0:
            print(f"  {priority}: {count}")
    print()
    print("PBIステータス:")
    for status, count in stats['pbis_by_status'].items():
        if count > 0:
            print(f"  {status}: {count}")
    print("=" * 60)
    
    # エラーサマリー
    if all_errors:
        print(f"\n⚠️  {len(all_errors)} 個のエラーが見つかりました:\n")
        for error in all_errors:
            print(f"  • {error}")
        sys.exit(1)
    else:
        print("\n✅ すべてのPBIファイルが正常に検証されました！")
        sys.exit(0)


if __name__ == '__main__':
    main()
