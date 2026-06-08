import type { Core } from '@strapi/strapi';

const config = ({ env }: Core.Config.Shared.ConfigParams): Core.Config.Plugin => {
  const cloudinaryEnabled = Boolean(
    env('CLOUDINARY_NAME') && env('CLOUDINARY_KEY') && env('CLOUDINARY_SECRET')
  );

  return {
    ...(cloudinaryEnabled
      ? {
          upload: {
            config: {
              provider: 'cloudinary',
              providerOptions: {
                cloud_name: env('CLOUDINARY_NAME'),
                api_key: env('CLOUDINARY_KEY'),
                api_secret: env('CLOUDINARY_SECRET'),
              },
              actionOptions: {
                upload: {
                  folder: env('CLOUDINARY_FOLDER', 'gezi-rehberi'),
                },
                uploadStream: {
                  folder: env('CLOUDINARY_FOLDER', 'gezi-rehberi'),
                },
                delete: {},
              },
            },
          },
        }
      : {}),
  };
};

export default config;
