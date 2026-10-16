// Structural rules outline data blocks without drawing a grid around every cell.
export const BORDER = '#BBC3CD';
export function frame(sheet, address) {
  const edge={style:'thin',color:BORDER};
  sheet.getRange(address).format.borders = {
    top:edge,bottom:edge,left:edge,right:edge,
    insideVertical:{style:'thin',color:'#DDE2E7'},
  };
}
export function header(sheet, address) {
  const f=sheet.getRange(address).format;
  f.fill='#F0F2F5'; f.font.bold=true; f.horizontalAlignment='center';
  f.borders={bottom:{style:'thin',color:BORDER}};
}
export function subtotal(sheet, address) {
  const f=sheet.getRange(address).format;
  f.font.bold=true; f.borders={top:{style:'thin',color:BORDER}};
}

export function documentationLinks(sheet) {
  // Downloads must link outside the repository checkout; a relative docs/ path is unusable there.
  const last=sheet.getUsedRange().values.length;
  const source=sheet.getRange(`C1:C${last}`);
  const values=source.values;
  for(let i=0;i<values.length;i++)if(typeof values[i][0]==='string' && values[i][0].startsWith('docs/')){
    sheet.getRange(`C${i+1}`).values=[['https://github.com/jackconnolly1000-ux/sec-filing-research-terminal/blob/main/'+values[i][0]]];
  }
}
