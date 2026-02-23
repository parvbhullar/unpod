import React from 'react';
import WriteThread from './WriteThread';
import UploadThread from './UploadThread';
import {useGetDataApi} from '@unpod/providers';

const POST_TYPE_CONTENT = {
  note: WriteThread,
  write: WriteThread,
  post_text: WriteThread,
  upload: UploadThread,
  post_video: UploadThread,
  post_audio: UploadThread,
};

const AddEditThread = ({threadType, ...restProps}) => {
  const [{apiData: tagsData}] = useGetDataApi(`core/tags/`, {});

  const TypeComponent = POST_TYPE_CONTENT[threadType];

  return TypeComponent && <TypeComponent tagsData={tagsData} {...restProps} />;
};

export default AddEditThread;
