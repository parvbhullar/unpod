export type PostWithOperations = {
  allowed_operations?: string[];};

export const isHostUser = (
  post: PostWithOperations | null | undefined,
): boolean => {
  return (post?.allowed_operations?.indexOf('start_stream') ?? -1) > -1;
};

export const isGuestUser = (
  post: PostWithOperations | null | undefined,
): boolean => {
  return (
    ((post?.allowed_operations?.indexOf('start_stream') ?? -1) === -1 &&
      (post?.allowed_operations?.indexOf('view_detail') ?? -1) > -1) ||
    true
  );
};
