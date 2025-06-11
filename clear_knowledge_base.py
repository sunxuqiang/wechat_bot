import os
import shutil
from pathlib import Path
import json

def get_knowledge_base_info():
    """获取知识库信息"""
    kb_dir = Path("knowledge_base")
    if not kb_dir.exists():
        return None
        
    info = {
        "index_exists": False,
        "docs_count": 0,
        "docs": [],
        "stats": None
    }
    
    # 检查索引文件
    index_file = kb_dir / "faiss_index"
    info["index_exists"] = index_file.exists()
    
    # 检查文档目录
    docs_dir = kb_dir / "docs"
    if docs_dir.exists():
        # 获取所有文档
        for doc in docs_dir.glob("**/*"):
            if doc.is_file():
                info["docs"].append({
                    "path": str(doc.relative_to(docs_dir)),
                    "size": doc.stat().st_size,
                    "modified": doc.stat().st_mtime
                })
        info["docs_count"] = len(info["docs"])
    
    # 读取统计信息
    stats_file = kb_dir / "stats.json"
    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                info["stats"] = json.load(f)
        except Exception:
            pass
            
    return info

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def delete_selected_content(selections):
    """删除选中的知识库内容"""
    try:
        kb_dir = Path("knowledge_base")
        if not kb_dir.exists():
            print("知识库目录不存在")
            return False
            
        files_deleted = []
        
        # 删除索引
        if "1" in selections:
            index_file = kb_dir / "faiss_index"
            if index_file.exists():
                shutil.rmtree(index_file)
                files_deleted.append("faiss_index")
        
        # 删除所有文档
        if "2" in selections:
            docs_dir = kb_dir / "docs"
            if docs_dir.exists():
                shutil.rmtree(docs_dir)
                docs_dir.mkdir(exist_ok=True)
                files_deleted.append("docs目录")
        
        # 删除特定文档
        elif "3" in selections:
            docs_dir = kb_dir / "docs"
            if docs_dir.exists():
                info = get_knowledge_base_info()
                if info and info["docs"]:
                    print("\n可删除的文档:")
                    for i, doc in enumerate(info["docs"], 1):
                        size = format_size(doc["size"])
                        print(f"{i}. {doc['path']} ({size})")
                    
                    while True:
                        doc_selections = input("\n请输入要删除的文档编号（多个用逗号分隔，直接回车取消）: ").strip()
                        if not doc_selections:
                            break
                            
                        try:
                            doc_nums = [int(x.strip()) for x in doc_selections.split(",")]
                            for num in doc_nums:
                                if 1 <= num <= len(info["docs"]):
                                    doc_path = docs_dir / info["docs"][num-1]["path"]
                                    if doc_path.exists():
                                        os.remove(doc_path)
                                        files_deleted.append(f"文档: {info['docs'][num-1]['path']}")
                            break
                        except ValueError:
                            print("输入无效，请重试")
        
        # 删除统计信息
        if "4" in selections:
            stats_file = kb_dir / "stats.json"
            if stats_file.exists():
                os.remove(stats_file)
                files_deleted.append("stats.json")
        
        if files_deleted:
            print("\n已删除的内容:")
            for item in files_deleted:
                print(f"- {item}")
            return True
        else:
            print("\n未删除任何内容")
            return False
            
    except Exception as e:
        print(f"\n删除过程中出错: {e}")
        return False

def show_menu():
    """显示菜单"""
    print("\n=== 知识库管理工具 ===")
    
    # 获取知识库信息
    info = get_knowledge_base_info()
    if info:
        print("\n当前知识库状态:")
        print(f"- 索引文件: {'存在' if info['index_exists'] else '不存在'}")
        print(f"- 文档数量: {info['docs_count']}个")
        if info["stats"]:
            print("- 知识库统计:")
            print(json.dumps(info["stats"], indent=2, ensure_ascii=False))
    else:
        print("\n知识库目录不存在")
        return
    
    print("\n可选操作:")
    print("1. 删除索引文件")
    print("2. 删除所有文档")
    print("3. 删除特定文档")
    print("4. 删除统计信息")
    print("5. 退出程序")

def main():
    while True:
        show_menu()
        selections = input("\n请选择要执行的操作（多个用逗号分隔）: ").strip()
        
        if not selections or "5" in selections:
            print("\n程序已退出")
            break
            
        if selections:
            confirm = input("确定要删除选中的内容吗？(y/N): ")
            if confirm.lower() == 'y':
                if delete_selected_content(selections.split(",")):
                    print("\n删除操作完成！")
                else:
                    print("\n删除操作失败或取消！")
            else:
                print("\n操作已取消")

if __name__ == "__main__":
    main() 