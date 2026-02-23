const hyphenToCamelcase = (str: string): string => {
  let result = '';
  let upper = false;

  for (let i = 0; i < str.length; i++) {
    let c = str[i];

    if (c === '-') {
      upper = true;
      continue;
    }

    if (upper) {
      c = c.toUpperCase();
      upper = false;
    }

    result += c;
  }

  return result;
};

const convertKey = (key: string): string => {
  let res = hyphenToCamelcase(key);

  if (key.startsWith('-ms-')) {
    res = res[0].toLowerCase() + res.slice(1);
  }

  return res;
};

export type StyleObject = {
  [key: string]: string;
};

const styleParser = (styleStr: string): StyleObject => {
  return styleStr
    .split(';')
    .reduce((res: string[], token: string) => {
      if (token.startsWith('base64,')) {
        res[res.length - 1] += ';' + token;
      } else {
        res.push(token);
      }
      return res;
    }, [])
    .reduce((obj: StyleObject, str: string) => {
      const tokens = str.split(':');
      const key = tokens[0].trim();
      if (key) {
        const value = tokens.slice(1).join(':').trim();
        obj[convertKey(key)] = value;
      }
      return obj;
    }, {});
};

export default styleParser;
