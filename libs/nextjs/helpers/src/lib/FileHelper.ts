export const getFileExtension = (
  filename: string | null | undefined,
): string => {
  const nameArray = filename?.split('.')?.reverse();

  return filename ? nameArray?.[0] || '' : '';
};

export const getFileName = (file: string): string => {
  const url = new URL(file);
  return url.pathname.split('/').pop() || '';
};

export const getBase64 = (
  img: Blob,
  callback: (result: string | ArrayBuffer | null) => void,
): void => {
  const reader = new FileReader();
  reader.addEventListener('load', () => callback(reader.result));
  reader.readAsDataURL(img);
};

export const downloadFile = (fileUrl: string): void => {
  const url = fileUrl;
  const e = document.createElement('a');
  e.href = url;
  e.target = '_blank';
  e.download = url.substr(url.lastIndexOf('/') + 1);
  document.body.appendChild(e);
  e.click();
  document.body.removeChild(e);
};

export const fileDownload = (
  data: Blob | BlobPart,
  filename: string,
  mimeType?: string,
): void => {
  let blob: Blob;
  if (data instanceof Blob) {
    blob = data;
  } else {
    blob = new Blob([data], { type: mimeType || 'application/octet-stream' });
  }
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;

  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
