import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import shutil
import os
from knowledge_bot import KnowledgeBot

class KnowledgeUploader:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("知识库文件上传")
        self.window.geometry("800x600")
        
        # 初始化知识库
        try:
            self.knowledge_bot = KnowledgeBot()
            self.supported_formats = list(self.knowledge_bot.loader_mapping.keys())
        except Exception as e:
            messagebox.showerror("错误", f"初始化知识库失败: {str(e)}")
            self.window.destroy()
            return
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 支持的文件格式标签
        ttk.Label(self.main_frame, text="支持的文件格式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        formats_text = ", ".join(self.supported_formats)
        ttk.Label(self.main_frame, text=formats_text).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # 选择文件按钮
        ttk.Button(self.main_frame, text="选择文件", command=self.select_files).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # 文件列表
        self.file_list_frame = ttk.LabelFrame(self.main_frame, text="待上传文件", padding="5")
        self.file_list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建文件列表的Treeview
        self.file_list = ttk.Treeview(self.file_list_frame, columns=("path", "status"), show="headings")
        self.file_list.heading("path", text="文件路径")
        self.file_list.heading("status", text="状态")
        self.file_list.column("path", width=500)
        self.file_list.column("status", width=100)
        self.file_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.file_list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        # 上传按钮
        ttk.Button(self.main_frame, text="上传到知识库", command=self.upload_files).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # 清空列表按钮
        ttk.Button(self.main_frame, text="清空列表", command=self.clear_list).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 知识库统计信息
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="知识库统计", padding="5")
        self.stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.update_stats()
        
        # 配置主窗口的网格权重
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.file_list_frame.columnconfigure(0, weight=1)
        self.file_list_frame.rowconfigure(0, weight=1)
    
    def select_files(self):
        """选择要上传的文件"""
        files = filedialog.askopenfilenames(
            title="选择要上传的文件",
            filetypes=[
                ("支持的文件", " ".join(f"*{ext}" for ext in self.supported_formats)),
                ("所有文件", "*.*")
            ]
        )
        
        for file_path in files:
            # 检查文件是否已在列表中
            existing_items = self.file_list.get_children()
            if not any(self.file_list.item(item)["values"][0] == file_path for item in existing_items):
                self.file_list.insert("", "end", values=(file_path, "待上传"))
    
    def upload_files(self):
        """上传文件到知识库"""
        items = self.file_list.get_children()
        if not items:
            messagebox.showinfo("提示", "请先选择要上传的文件")
            return
        
        success_count = 0
        for item in items:
            values = self.file_list.item(item)["values"]
            file_path = values[0]
            if values[1] != "已上传":
                try:
                    # 上传文件到知识库
                    if self.knowledge_bot.add_document(file_path):
                        self.file_list.item(item, values=(file_path, "已上传"))
                        success_count += 1
                    else:
                        self.file_list.item(item, values=(file_path, "上传失败"))
                except Exception as e:
                    self.file_list.item(item, values=(file_path, "上传失败"))
                    messagebox.showerror("错误", f"上传文件 {file_path} 失败: {str(e)}")
        
        # 更新统计信息
        self.update_stats()
        
        # 显示上传结果
        messagebox.showinfo("上传完成", f"成功上传 {success_count} 个文件")
    
    def clear_list(self):
        """清空文件列表"""
        self.file_list.delete(*self.file_list.get_children())
    
    def update_stats(self):
        """更新知识库统计信息"""
        try:
            # 清空原有的统计信息
            for widget in self.stats_frame.winfo_children():
                widget.destroy()
            
            # 获取最新统计信息
            stats = self.knowledge_bot.get_statistics()
            
            # 显示统计信息
            ttk.Label(self.stats_frame, text=f"文档总数: {stats.get('total_documents', 0)}").grid(row=0, column=0, sticky=tk.W, padx=5)
            ttk.Label(self.stats_frame, text=f"文本块总数: {stats.get('total_chunks', 0)}").grid(row=0, column=1, sticky=tk.W, padx=5)
            
            # 显示文档列表
            if stats.get('documents'):
                docs_text = "文档列表:\n"
                for doc in stats['documents']:
                    docs_text += f"- {doc['path']} (块数: {doc['chunk_count']})\n"
                ttk.Label(self.stats_frame, text=docs_text).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)
        except Exception as e:
            messagebox.showerror("错误", f"更新统计信息失败: {str(e)}")
    
    def run(self):
        """运行GUI程序"""
        self.window.mainloop()

if __name__ == "__main__":
    app = KnowledgeUploader()
    app.run() 