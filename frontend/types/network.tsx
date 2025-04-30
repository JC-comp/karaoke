interface NetPacket<T> {
  success: boolean;
  message: string;
  body: T;
}