"""Consistent method labels and best-value emphasis at the displayed precision."""
from decimal import Decimal, InvalidOperation

NAMES={
 'M1':('纯视觉 + Astra','RGB-only + Astra'),
 'M2':('ViPE + Astra','ViPE + Astra'),
 'M3':('OpenVINS + MapAnything + Astra','OpenVINS + MapAnything + Astra'),
 'M4':('GT 位姿 + MapAnything + Astra','GT pose + MapAnything + Astra'),
 'B1':('ViPE + TSDF','ViPE + TSDF'),
 'B2':('MapAnything + TSDF','MapAnything + TSDF'),
 'B2p':('OpenVINS + MapAnything + TSDF','OpenVINS + MapAnything + TSDF'),
}

def method_label(method,zh):
 return method+' · '+NAMES[method][0 if zh else 1]

def best_values(rows,directions):
 """Emphasize extrema of displayed numeric cells; exclude GT input and missing cells.

 Directions map zero-based column index to min/max. Equal displayed values all
 receive emphasis; different units and different task criteria never get pooled.
 """
 output=[list(row) for row in rows]
 for col,direction in directions.items():
  assert direction in ('min','max')
  candidates=[]
  for index,row in enumerate(rows):
   try:value=Decimal(str(row[col]).rstrip('%'))
   except InvalidOperation:continue
   if value.is_finite():candidates.append((index,value))
  if not candidates:continue
  best=(min if direction=='min' else max)(value for _,value in candidates)
  for index,value in candidates:
   if value==best:output[index][col]='**'+str(rows[index][col])+'**'
 return output

def legend(zh):
 return ('**粗体**表示各指标列的最佳显示值；按表内精度判定，并列值均加粗。↓ 越低越好，↑ 越高越好；GT 输入与缺失值不参与排名。' if zh else '**Bold** marks the best displayed value in each metric column; ties at the shown precision are all bold. ↓ Lower is better; ↑ higher is better. GT inputs and missing values are excluded.')
