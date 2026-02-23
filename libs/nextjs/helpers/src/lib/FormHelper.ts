import {capitalizedString} from './StringHelper';

export const parseRegex = (
  regexString: string | null | undefined,
): RegExp | null => {
  if (!regexString) return null;

  const match = regexString.match(/^\/(.+)\/([gimsuy]*)$/);
  if (match) {
    return new RegExp(match[1], match[2]); // pattern, flags
  }

  return new RegExp(regexString);
};

export type FieldDependency = {
  depends_on: string;
  value: unknown;
  condition?: string;
};

export const fieldDependencyResolved = (
  dependencies: FieldDependency[] | null | undefined,
  getFieldValue: (name: string) => unknown,
): FieldDependency[] => {
  if (!Array.isArray(dependencies) || dependencies.length === 0) {
    return [];
  }
  const resolved: FieldDependency[] = [];
  dependencies.forEach((item) => {
    const currentValue = getFieldValue(item.depends_on);
    if (isFieldValidCondition(currentValue, item.value, item.condition))
      resolved.push(item);
  });
  return resolved;
};

export const isFieldDependencyResolved = (
  dependencies: FieldDependency[],
  getFieldValue: (name: string) => unknown,
): boolean => {
  const resolveItems = fieldDependencyResolved(dependencies, getFieldValue);
  return dependencies.length > 0 && resolveItems.length === dependencies.length;
};

export const isFieldValidCondition = (
  currentValue: unknown,
  valueOfCheck: unknown,
  condition = 'equals',
): boolean => {
  switch (condition) {
    case 'equals':
      return currentValue == valueOfCheck;
    case 'not_equals':
      return currentValue != valueOfCheck;
    case 'starts_with':
      return String(currentValue).startsWith(String(valueOfCheck));
    case 'ends_with':
      return String(currentValue).endsWith(String(valueOfCheck));
    case 'is_empty':
      return currentValue === '' || currentValue == null;
    case 'is_not_empty':
      return currentValue !== '' && currentValue != null;
    case 'contains':
      return String(currentValue).includes(String(valueOfCheck));
    case 'not_contains':
      return !String(currentValue).includes(String(valueOfCheck));
  }

  return false;
};

export type FormField = {
  title?: string;
  required?: boolean;
  type?: string;
  regex?: string;
  regexMessage?: string;
};

export type ValidationRule = {
  required?: boolean;
  message?: string;
  type?: string;
  pattern?: RegExp;
  validator?: (rule: unknown, value: unknown) => Promise<void>;
};

export const getFieldValidationRules = (field: FormField): ValidationRule[] => {
  const label = capitalizedString(field?.title?.toLowerCase());
  const rules: ValidationRule[] = [];
  if (field.required) {
    rules.push({
      required: true,
      message: `${label || 'This field'} is required.`,
    });
  }
  if (field.type === 'email') {
    rules.push({
      type: 'email',
      message: `Please enter a valid email address.`,
    });
  }
  if (field.type === 'number') {
    rules.push({pattern: /^\d+$/, message: `Please enter a valid number.`});
  }
  if (field.regex) {
    rules.push({
      validator: (_: unknown, v: unknown) => {
        if (!v) return Promise.resolve();
        const regex = parseRegex(field.regex);
        return regex && regex.test(String(v))
          ? Promise.resolve()
          : Promise.reject(
            new Error(
              field.regexMessage || `Enter a valid ${label.toLowerCase()}`,
            ),
          );
      },
    });
  }
  if (field.type === 'url' && !field.regex) {
    rules.push({
      type: 'url',
      message: `Please enter a valid ${label.toLowerCase()}`,
    });
  }
  return rules;
};
