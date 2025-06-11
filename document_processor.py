import os
import pandas as pd
from typing import List, Dict, Any, Optional
from pptx import Presentation
from openpyxl import load_workbook
from docx import Document
from PyPDF2 import PdfReader
import magic
import logging
from dataclasses import dataclass
from tqdm import tqdm
from loguru import logger
import traceback

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """文档分块类，用于存储文档内容和元数据"""
    content: str  # 文档内容
    metadata: Dict[str, Any]  # 元数据（如来源、类型等）

class DocumentProcessor:
    """文档处理器，支持多种文件格式的读取和处理"""
    
    SUPPORTED_EXTENSIONS = {
        # 文本文件
        '.txt': 'text/plain',
        # Microsoft Office
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.xls': 'application/vnd.ms-excel',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.doc': 'application/msword',
        # PDF
        '.pdf': 'application/pdf',
        # 其他文本格式
        '.md': 'text/markdown',
        '.csv': 'text/csv',
        '.json': 'application/json',
    }

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档处理器
        :param chunk_size: 文本分块大小
        :param chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """
        处理单个文件
        :param file_path: 文件路径
        :return: 文档分块列表
        """
        try:
            # 检测文件类型
            file_type = magic.from_file(file_path, mime=True)
            extension = os.path.splitext(file_path)[1].lower()

            # 验证文件类型
            if extension not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported file extension: {extension}")

            # 根据文件类型调用相应的处理方法
            if extension in ['.xlsx', '.xls']:
                return self._process_excel(file_path)
            elif extension in ['.pptx', '.ppt']:
                return self._process_powerpoint(file_path)
            elif extension in ['.docx', '.doc']:
                return self._process_word(file_path)
            elif extension == '.pdf':
                return self._process_pdf(file_path)
            elif extension == '.csv':
                return self._process_csv(file_path)
            else:  # 处理纯文本文件
                return self._process_text(file_path)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise

    def _process_excel(self, file_path: str) -> List[DocumentChunk]:
        """处理Excel文件"""
        chunks = []
        try:
            logger.info(f"开始处理Excel文件: {file_path}")
            
            # 使用pandas读取Excel文件
            logger.info("读取Excel文件...")
            excel_file = pd.ExcelFile(file_path)
            logger.info(f"发现 {len(excel_file.sheet_names)} 个工作表: {excel_file.sheet_names}")
            
            # 处理每个工作表
            for sheet_name in excel_file.sheet_names:
                logger.info(f"\n处理工作表: {sheet_name}")
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 获取表头
                headers = df.columns.tolist()
                logger.info(f"列名: {headers}")
                logger.info(f"数据行数: {len(df)}")
                
                # 处理每一行
                for index, row in df.iterrows():
                    # 构建行文本
                    row_text = " | ".join([f"{headers[i]}: {str(row[i])}" for i in range(len(headers))])
                    
                    metadata = {
                        'source': file_path,
                        'sheet_name': sheet_name,
                        'row_index': index,
                        'type': 'excel'
                    }
                    
                    logger.debug(f"行 {index + 1}:")
                    logger.debug(f"- 文本: {row_text}")
                    logger.debug(f"- 元数据: {metadata}")
                    
                    chunks.append(DocumentChunk(content=row_text, metadata=metadata))
                
                # 添加表格概述
                summary = f"工作表 '{sheet_name}' 包含 {len(df)} 行数据，列名为：{', '.join(headers)}"
                metadata = {
                    'source': file_path,
                    'sheet_name': sheet_name,
                    'type': 'excel_summary'
                }
                
                logger.info(f"添加表格概述: {summary}")
                chunks.append(DocumentChunk(content=summary, metadata=metadata))
                
            logger.info(f"Excel处理完成，共生成 {len(chunks)} 个文本块")
            
            # 记录一些示例块
            if chunks:
                logger.info("\n文本块示例:")
                for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
                    logger.info(f"块 {i+1}:")
                    logger.info(f"- 内容: {chunk.content}")
                    logger.info(f"- 元数据: {chunk.metadata}")
            
        except Exception as e:
            logger.error(f"处理Excel文件时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
        return chunks

    def _process_powerpoint(self, file_path: str) -> List[DocumentChunk]:
        """处理PowerPoint文件"""
        chunks = []
        try:
            presentation = Presentation(file_path)
            
            for slide_number, slide in enumerate(presentation.slides, 1):
                slide_text = []
                
                # 处理标题
                if slide.shapes.title:
                    slide_text.append(f"标题: {slide.shapes.title.text}")
                
                # 处理其他形状中的文本
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                
                if slide_text:
                    content = "\n".join(slide_text)
                    metadata = {
                        'source': file_path,
                        'slide_number': slide_number,
                        'type': 'powerpoint'
                    }
                    chunks.append(DocumentChunk(content=content, metadata=metadata))
                
            # 添加PPT概述
            summary = f"演示文稿包含 {len(presentation.slides)} 张幻灯片"
            metadata = {
                'source': file_path,
                'type': 'powerpoint_summary'
            }
            chunks.append(DocumentChunk(content=summary, metadata=metadata))
            
        except Exception as e:
            logger.error(f"Error processing PowerPoint file {file_path}: {str(e)}")
            raise
            
        return chunks

    def _process_word(self, file_path: str) -> List[DocumentChunk]:
        """处理Word文件"""
        chunks = []
        try:
            doc = Document(file_path)
            current_chunk = []
            current_length = 0
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                    
                # 如果当前块加上新段落超过块大小，创建新块
                if current_length + len(text) > self.chunk_size:
                    if current_chunk:
                        content = "\n".join(current_chunk)
                        metadata = {
                            'source': file_path,
                            'type': 'word'
                        }
                        chunks.append(DocumentChunk(content=content, metadata=metadata))
                    current_chunk = [text]
                    current_length = len(text)
                else:
                    current_chunk.append(text)
                    current_length += len(text)
            
            # 处理最后一个块
            if current_chunk:
                content = "\n".join(current_chunk)
                metadata = {
                    'source': file_path,
                    'type': 'word'
                }
                chunks.append(DocumentChunk(content=content, metadata=metadata))
                
        except Exception as e:
            logger.error(f"Error processing Word file {file_path}: {str(e)}")
            raise
            
        return chunks

    def _process_pdf(self, file_path: str) -> List[DocumentChunk]:
        """处理PDF文件"""
        chunks = []
        try:
            reader = PdfReader(file_path)
            current_chunk = []
            current_length = 0
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text().strip()
                if not text:
                    continue
                
                # 按句子分割文本
                sentences = text.split('。')
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                        
                    # 如果当前块加上新句子超过块大小，创建新块
                    if current_length + len(sentence) > self.chunk_size:
                        if current_chunk:
                            content = "。".join(current_chunk) + "。"
                            metadata = {
                                'source': file_path,
                                'page_number': page_num,
                                'type': 'pdf'
                            }
                            chunks.append(DocumentChunk(content=content, metadata=metadata))
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += len(sentence)
            
            # 处理最后一个块
            if current_chunk:
                content = "。".join(current_chunk) + "。"
                metadata = {
                    'source': file_path,
                    'page_number': page_num,
                    'type': 'pdf'
                }
                chunks.append(DocumentChunk(content=content, metadata=metadata))
                
        except Exception as e:
            logger.error(f"Error processing PDF file {file_path}: {str(e)}")
            raise
            
        return chunks

    def _process_csv(self, file_path: str) -> List[DocumentChunk]:
        """处理CSV文件"""
        chunks = []
        try:
            df = pd.read_csv(file_path)
            headers = df.columns.tolist()
            
            # 处理每一行
            for index, row in df.iterrows():
                # 构建行文本
                row_text = " | ".join([f"{headers[i]}: {str(row[i])}" for i in range(len(headers))])
                
                metadata = {
                    'source': file_path,
                    'row_index': index,
                    'type': 'csv'
                }
                
                chunks.append(DocumentChunk(content=row_text, metadata=metadata))
            
            # 添加CSV概述
            summary = f"CSV文件包含 {len(df)} 行数据，列名为：{', '.join(headers)}"
            metadata = {
                'source': file_path,
                'type': 'csv_summary'
            }
            chunks.append(DocumentChunk(content=summary, metadata=metadata))
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise
            
        return chunks

    def _process_text(self, file_path: str) -> List[DocumentChunk]:
        """处理文本文件"""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                
            # 按段落分割
            paragraphs = text.split('\n\n')
            current_chunk = []
            current_length = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                    
                # 如果当前块加上新段落超过块大小，创建新块
                if current_length + len(para) > self.chunk_size:
                    if current_chunk:
                        content = "\n".join(current_chunk)
                        metadata = {
                            'source': file_path,
                            'type': 'text'
                        }
                        chunks.append(DocumentChunk(content=content, metadata=metadata))
                    current_chunk = [para]
                    current_length = len(para)
                else:
                    current_chunk.append(para)
                    current_length += len(para)
            
            # 处理最后一个块
            if current_chunk:
                content = "\n".join(current_chunk)
                metadata = {
                    'source': file_path,
                    'type': 'text'
                }
                chunks.append(DocumentChunk(content=content, metadata=metadata))
                
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            raise
            
        return chunks

    def process_directory(self, directory_path: str) -> List[DocumentChunk]:
        """
        处理目录下的所有支持的文件
        :param directory_path: 目录路径
        :return: 所有文档分块的列表
        """
        all_chunks = []
        
        # 获取所有文件
        files = []
        for root, _, filenames in os.walk(directory_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(root, filename))
        
        # 使用tqdm显示处理进度
        for file_path in tqdm(files, desc="Processing documents"):
            try:
                chunks = self.process_file(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
        
        return all_chunks 