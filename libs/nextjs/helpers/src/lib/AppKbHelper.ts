import { getMachineName } from './StringHelper';
import { randomId } from './GlobalHelper';

export type InputSchemaProperty = {
  title?: string;
  type?: string;
  description?: string;
  enum?: string[];
  defaultValue?: unknown;
};

export type InputSchema = {
  properties?: Record<string, InputSchemaProperty>;
  required?: string[];
};

export type KbInput = {
  id: number;
  name: string;
  title: string;
  type: string | undefined;
  description: string | undefined;
  required: boolean;
  choices: string[];
  isEnum: boolean;
  defaultValue: unknown;
};

export const getKbInputsStructure = (
  inputSchema: InputSchema | null | undefined,
): KbInput[] => {
  if (inputSchema?.properties)
    return Object.keys(inputSchema.properties).map((key) => {
      const input = inputSchema.properties![key];

      return {
        id: randomId(),
        name: key,
        title: input.title || key,
        type: input.type,
        description: input.description,
        required: inputSchema?.required?.includes(key) || false,
        choices: input.enum || [],
        isEnum:
          !!input.enum &&
          input.enum.length > 0 &&
          (input.type === 'string' || input.type === 'text'),
        defaultValue: input.defaultValue,
      };
    });
  return [];
};

export type GeneratedSchemaProperty = {
  type: string | undefined;
  title: string | undefined;
  description: string;
  defaultValue: string;
  enum?: string[];
};

export type GeneratedSchema = {
  type: 'object';
  properties: Record<string, GeneratedSchemaProperty>;
  required: string[];
};

export type KbInputForSchema = {
  name?: string;
  type?: string;
  title?: string;
  description?: string;
  defaultValue?: string;
  isEnum?: boolean;
  choices?: string[];
  required?: boolean;
};

export const generateKbSchema = (
  inputs: KbInputForSchema[],
): GeneratedSchema => {
  const schema: GeneratedSchema = {
    type: 'object',
    properties: {},
    required: [],
  };
  const filteredInputs = inputs.filter((input) => input.name) || [];

  for (let i = 0; i < filteredInputs.length; i++) {
    const input = filteredInputs[i];
    const name = getMachineName(input.name || '');

    schema.properties[name] = {
      type: input.type,
      title: input.title,
      description: input.description || '',
      defaultValue: input.defaultValue || '',
    };

    if (
      (input.type === 'select' ||
        input.type === 'multi-select' ||
        input.type === 'checkboxes' ||
        input.isEnum) &&
      input.choices &&
      input.choices.length > 0
    ) {
      schema.properties[name].enum = input.choices || [];
    }

    if (input.required) {
      schema.required.push(name);
    }
  }

  return schema;
};
