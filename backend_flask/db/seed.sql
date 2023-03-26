-- this file was manually created
INSERT INTO public.users (display_name, email, handle, cognito_user_id)
VALUES
  ('Armando Diaz', 'arm.dan.diaz.gonzalez@gmail.com', 'armandodiaz' ,'MOCK'),
  ('Daniel Diaz', 'addiazgonzalez@csustudent.net', 'danieldiaz' ,'MOCK');
    ('Londo Mollari','lmollari@centari.com' ,'londo' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'armandodiaz' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )