// Structural rules outline data blocks without drawing a grid around every cell.
export const BORDER = '#BBC3CD';
export function frame(sheet, address) {
  sheet.getRange(address).format.borders = {preset:'outside',style:'thin',color:BORDER};
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
