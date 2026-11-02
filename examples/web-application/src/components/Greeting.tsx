interface GreetingProps {
  name: string;
}

export function Greeting({ name }: GreetingProps): JSX.Element {
  if (!name) {
    return <p>Hello, stranger!</p>;
  }
  return <p>Hello, {name}!</p>;
}
